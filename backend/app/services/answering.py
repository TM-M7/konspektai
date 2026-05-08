from __future__ import annotations

import logging
import re

import httpx

from app.config import AppConfig
from app.db import Database
from app.schemas import AIAnswerRecord, TranscriptSegment


logger = logging.getLogger(__name__)


class AnswerGenerationError(Exception):
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

        text = self._generate_answer_text(segment.text, segment.language)
        return self._save_answer(segment.question_id, segment, text)

    async def generate_for_question_id(self, question_id: int) -> AIAnswerRecord:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    questions.id AS question_id,
                    questions.session_id AS session_id,
                    questions.segment_id AS segment_id,
                    questions.text AS question_text,
                    transcript_segments.language AS language,
                    transcript_segments.ts AS timestamp
                FROM questions
                JOIN transcript_segments ON transcript_segments.id = questions.segment_id
                WHERE questions.id = ?
                """,
                (question_id,),
            ).fetchone()

        if row is None:
            raise AnswerGenerationError("unknown_question")

        segment = TranscriptSegment(
            id=row["segment_id"],
            session_id=row["session_id"],
            timestamp=row["timestamp"],
            language=row["language"],
            text=row["question_text"],
            confidence=1.0,
            phrase_type="question",
            priority="high",
            show_answer=True,
            question_id=row["question_id"],
        )
        return await self.generate_for_segment(segment)

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

    def _generate_answer_text(self, question_text: str, language: str) -> str:
        text = question_text.strip()
        if not text:
            raise AnswerGenerationError("empty_question")

        answer = self._generate_ollama_answer(text, language) if self.config.answer_mode == "ollama" else build_stub_answer(text, language)
        if not answer:
            raise AnswerGenerationError("empty_answer")
        return answer

    def _generate_ollama_answer(self, question_text: str, language: str) -> str:
        prompt = build_ollama_prompt(question_text, language)
        try:
            with httpx.Client(timeout=self.config.ollama_timeout_seconds) as client:
                response = client.post(
                    f"{self.config.ollama_base_url}/api/generate",
                    json={"model": self.config.ollama_model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AnswerGenerationError("ollama_timeout") from exc
        except httpx.HTTPError as exc:
            raise AnswerGenerationError("ollama_unavailable") from exc

        payload = response.json()
        text = str(payload.get("response", "")).strip()
        if not text:
            raise AnswerGenerationError("empty_answer")
        return text

    def _save_answer(self, question_id: int, segment: TranscriptSegment, text: str) -> AIAnswerRecord:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO answers(question_id, language, text) VALUES (?, ?, ?)",
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


def build_stub_answer(question_text: str, language: str) -> str:
    normalized = question_text.lower()
    if "raid 0" in normalized and "raid 1" in normalized:
        return (
            "DE: RAID 0 ist schneller, aber ohne Redundanz. RAID 1 spiegelt Daten und ist sicherer.\n"
            "RU: RAID 0 bystree, no bez otkazoustoichivosti. RAID 1 zerkaliruet dannye i nadezhnee."
        )
    if "raid 1" in normalized:
        return (
            "DE: RAID 1 spiegelt Daten auf zwei Laufwerken, damit ein Laufwerk ausfallen kann.\n"
            "RU: RAID 1 zerkaliruet dannye na dva diska dlya povysheniya nadezhnosti."
        )
    if "dns" in normalized:
        return (
            "DE: DNS ubersetzt Domainnamen in IP-Adressen.\n"
            "RU: DNS perevodit domennye imena v IP-adresa."
        )
    if language.lower().startswith("de"):
        cleaned = re.sub(r"[?]+$", "", question_text).strip()
        return (
            f"DE: Kurzantwort zu '{cleaned}': Das ist ein zentraler Begriff aus dem Unterricht und sollte knapp erklart werden.\n"
            "RU: Korotkii otvet: eto vazhnyi termin iz uroka, ego nuzhno obyasnyat kratko i po suti."
        )
    cleaned = re.sub(r"[?]+$", "", question_text).strip()
    return (
        f"Short answer for '{cleaned}': this is an important study concept, explain it briefly and clearly.\n"
        "RU: Korotkii otvet: eto vazhnoe uchebnoe ponyatie, ego stoit obyasnyat kratko i yasno."
    )


def build_ollama_prompt(question_text: str, language: str) -> str:
    german = language.lower().startswith("de")
    instruction = (
        "If the question is German, answer in German first, then add a short Russian translation."
        if german
        else "Answer shortly and clearly in the original language. Add short Russian help only if useful."
    )
    return "\n".join(
        [
            "School context.",
            "Answer shortly and clearly.",
            "Keep the answer within 3 to 5 lines.",
            "Do not invent context.",
            instruction,
            "",
            f"Question: {question_text}",
        ]
    )
