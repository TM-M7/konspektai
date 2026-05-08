from __future__ import annotations

import logging

import httpx

from app.config import AppConfig
from app.db import Database
from app.schemas import AIAnswerRecord, TranscriptSegment


logger = logging.getLogger(__name__)


class AnswerGenerationError(Exception):
    """Raised when an AI answer could not be generated."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class QuestionAnswerService:
    def __init__(self, database: Database, config: AppConfig) -> None:
        self.database = database
        self.config = config

    async def generate_for_segment(self, segment: TranscriptSegment) -> AIAnswerRecord:
        if segment.question_id is None:
            raise AnswerGenerationError("missing_question_id")

        prompt = build_answer_prompt(segment.text, segment.language)
        text = await self._generate_answer_text(prompt)
        return self._save_answer(
            question_id=segment.question_id,
            segment=segment,
            text=text,
        )

    def list_answers(self, session_id: int) -> list[AIAnswerRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    answers.id AS id,
                    questions.session_id AS session_id,
                    answers.question_id AS question_id,
                    questions.segment_id AS segment_id,
                    questions.text AS question_text,
                    answers.language AS language,
                    answers.text AS text
                FROM answers
                JOIN questions ON questions.id = answers.question_id
                WHERE questions.session_id = ?
                ORDER BY answers.id ASC
                """,
                (session_id,),
            ).fetchall()

        return [
            AIAnswerRecord(
                id=row["id"],
                session_id=row["session_id"],
                question_id=row["question_id"],
                segment_id=row["segment_id"],
                question_text=row["question_text"],
                language=row["language"],
                text=row["text"],
            )
            for row in rows
        ]

    async def _generate_answer_text(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.config.ollama_timeout_seconds) as client:
                response = await client.post(
                    f"{self.config.ollama_base_url}/api/generate",
                    json={
                        "model": self.config.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AnswerGenerationError("timeout") from exc
        except httpx.HTTPError as exc:
            raise AnswerGenerationError("ollama_unavailable") from exc

        payload = response.json()
        text = str(payload.get("response", "")).strip()
        if not text:
            raise AnswerGenerationError("empty_answer")
        return text

    def _save_answer(
        self,
        question_id: int,
        segment: TranscriptSegment,
        text: str,
    ) -> AIAnswerRecord:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO answers(question_id, language, text)
                VALUES (?, ?, ?)
                """,
                (question_id, segment.language, text),
            )
            connection.commit()
            answer_id = int(cursor.lastrowid)

        logger.info("AI answer stored: question=%s answer=%s", question_id, answer_id)
        return AIAnswerRecord(
            id=answer_id,
            session_id=segment.session_id,
            question_id=question_id,
            segment_id=segment.id,
            question_text=segment.text,
            language=segment.language,
            text=text,
        )


def build_answer_prompt(question_text: str, language: str) -> str:
    is_german = language.lower().startswith("de")
    answer_instruction = (
        "If the question is German, answer in German first, then provide a short Russian translation."
        if is_german
        else "Answer shortly and clearly in the original language. Add a short Russian translation only when useful."
    )
    return "\n".join(
        [
            "School context.",
            "Answer shortly and clearly.",
            answer_instruction,
            "Do not invent context.",
            "Keep the answer within 3 to 5 lines.",
            "",
            f"Question: {question_text}",
        ]
    )
