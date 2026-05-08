from __future__ import annotations

import logging
import sqlite3
from collections import deque

from app.config import AppConfig
from app.db import Database
from app.schemas import AIAnswerRecord, IngestResponse, TranscriptIngestRequest, TranscriptSegment
from app.services.classifier import classify_phrase


logger = logging.getLogger(__name__)


class TranscriptPipeline:
    def __init__(self, database: Database, config: AppConfig) -> None:
        self.database = database
        self.config = config
        self._recent_texts: deque[str] = deque(maxlen=config.duplicate_window_size)

    def create_session(self, title: str) -> dict:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO sessions(title) VALUES (?)",
                (title,),
            )
            connection.commit()
            session_id = int(cursor.lastrowid)
        logger.info("Session created: id=%s title=%s", session_id, title)
        return {"id": session_id, "title": title}

    def ingest(self, payload: TranscriptIngestRequest) -> IngestResponse:
        text = payload.text.strip()
        if not text:
            return IngestResponse(accepted=False, reason="empty_text")

        if payload.confidence < self.config.min_confidence:
            return IngestResponse(accepted=False, reason="low_confidence")

        if payload.volume is not None:
            volume_state = self._evaluate_volume(payload.volume)
            if volume_state != "ok":
                return IngestResponse(accepted=False, reason=volume_state)

        if self._is_duplicate(text):
            return IngestResponse(accepted=False, reason="duplicate")

        if not self._session_exists(payload.session_id):
            return IngestResponse(accepted=False, reason="unknown_session")

        classification = classify_phrase(text)
        question_id: int | None = None

        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO transcript_segments(
                    session_id, ts, language, text, confidence, phrase_type, priority, show_answer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.session_id,
                    payload.timestamp,
                    payload.language,
                    text,
                    payload.confidence,
                    classification.phrase_type,
                    classification.priority,
                    int(classification.show_answer),
                ),
            )
            segment_id = int(cursor.lastrowid)

            if classification.phrase_type == "question":
                question_cursor = connection.execute(
                    """
                    INSERT INTO questions(session_id, segment_id, text)
                    VALUES (?, ?, ?)
                    """,
                    (payload.session_id, segment_id, text),
                )
                question_id = int(question_cursor.lastrowid)

            connection.commit()

        self._recent_texts.append(text.casefold())
        logger.info(
            "Segment stored: session=%s segment=%s type=%s",
            payload.session_id,
            segment_id,
            classification.phrase_type,
        )
        return IngestResponse(
            accepted=True,
            segment=TranscriptSegment(
                id=segment_id,
                session_id=payload.session_id,
                timestamp=payload.timestamp,
                language=payload.language,
                text=text,
                confidence=payload.confidence,
                phrase_type=classification.phrase_type,
                priority=classification.priority,
                show_answer=classification.show_answer,
                question_id=question_id,
            ),
        )

    def list_segments(self, session_id: int) -> list[TranscriptSegment]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, ts, language, text, confidence, phrase_type, priority, show_answer
                FROM transcript_segments
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return [
            TranscriptSegment(
                id=row["id"],
                session_id=row["session_id"],
                timestamp=row["ts"],
                language=row["language"],
                text=row["text"],
                confidence=row["confidence"],
                phrase_type=row["phrase_type"],
                priority=row["priority"],
                show_answer=bool(row["show_answer"]),
                question_id=self._lookup_question_id(row["id"]),
            )
            for row in rows
        ]

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

    def _is_duplicate(self, text: str) -> bool:
        return text.casefold() in self._recent_texts

    def _session_exists(self, session_id: int) -> bool:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return row is not None

    def _lookup_question_id(self, segment_id: int) -> int | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id FROM questions WHERE segment_id = ?",
                (segment_id,),
            ).fetchone()
        if row is None:
            return None
        return int(row["id"])

    def _evaluate_volume(self, volume: float) -> str:
        if volume < self.config.low_volume_threshold:
            return "silence"
        if volume > self.config.high_volume_threshold:
            return "too_loud"
        return "ok"
