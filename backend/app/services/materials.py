from __future__ import annotations

import csv
import re
from pathlib import Path

from app.config import AppConfig
from app.db import Database
from app.schemas import ExportRecord, FlashcardRecord


class StudyMaterialsService:
    def __init__(self, database: Database, config: AppConfig) -> None:
        self.database = database
        self.config = config

    def generate_flashcards(self, session_id: int) -> list[FlashcardRecord]:
        self._get_session(session_id)
        cards = self._build_flashcards(session_id)

        with self.database.connect() as connection:
            connection.execute("DELETE FROM flashcards WHERE session_id = ?", (session_id,))
            for card in cards:
                connection.execute(
                    """
                    INSERT INTO flashcards(session_id, front_text, back_text)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, card["front_text"], card["back_text"]),
                )
            connection.commit()

        return self.list_flashcards(session_id)

    def list_flashcards(self, session_id: int) -> list[FlashcardRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, front_text, back_text
                FROM flashcards
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return [
            FlashcardRecord(
                id=row["id"],
                session_id=row["session_id"],
                front_text=row["front_text"],
                back_text=row["back_text"],
            )
            for row in rows
        ]

    def export_markdown(self, session_id: int) -> ExportRecord:
        session = self._get_session(session_id)
        segments = self._get_segments(session_id)
        answers = self._get_answers(session_id)
        flashcards = self.list_flashcards(session_id)

        output_path = self._build_export_path(session_id, session["title"], "notes", ".md")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# {session['title']}",
            "",
            f"Session ID: {session_id}",
            "",
            "## Transcript",
            "",
        ]
        for segment in segments:
            lines.append(
                f"- [{segment['ts']}] ({segment['phrase_type']}) {segment['text']}"
            )

        lines.extend(["", "## Questions and Answers", ""])
        if answers:
            for answer in answers:
                lines.append(f"### {answer['question_text']}")
                lines.append("")
                lines.append(answer["text"])
                lines.append("")
        else:
            lines.append("No saved answers yet.")

        lines.extend(["", "## Flashcards", ""])
        if flashcards:
            for card in flashcards:
                lines.append(f"- Front: {card.front_text}")
                lines.append(f"  Back: {card.back_text}")
        else:
            lines.append("No flashcards generated yet.")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return self._store_export_record(session_id, "markdown", output_path)

    def export_anki_csv(self, session_id: int) -> ExportRecord:
        session = self._get_session(session_id)
        flashcards = self.list_flashcards(session_id)
        output_path = self._build_export_path(session_id, session["title"], "anki", ".csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            for card in flashcards:
                writer.writerow([card.front_text, card.back_text])

        return self._store_export_record(session_id, "anki_csv", output_path)

    def list_exports(self, session_id: int) -> list[ExportRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, export_type, path
                FROM exports
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return [
            ExportRecord(
                id=row["id"],
                session_id=row["session_id"],
                export_type=row["export_type"],
                path=row["path"],
            )
            for row in rows
        ]

    def _build_flashcards(self, session_id: int) -> list[dict[str, str]]:
        answers = self._get_answers(session_id)
        definitions = self._get_definitions(session_id)
        seen = set()
        cards: list[dict[str, str]] = []

        for answer in answers:
            card = {
                "front_text": answer["question_text"],
                "back_text": answer["text"],
            }
            key = (card["front_text"], card["back_text"])
            if key not in seen:
                seen.add(key)
                cards.append(card)

        for definition in definitions:
            term = extract_definition_term(definition["text"])
            if not term:
                continue
            card = {
                "front_text": f"What is {term}?",
                "back_text": definition["text"],
            }
            key = (card["front_text"], card["back_text"])
            if key not in seen:
                seen.add(key)
                cards.append(card)

        return cards

    def _get_session(self, session_id: int):
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, title FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Unknown session: {session_id}")
        return row

    def _get_segments(self, session_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT ts, text, phrase_type
                FROM transcript_segments
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

    def _get_definitions(self, session_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT text
                FROM transcript_segments
                WHERE session_id = ? AND phrase_type = 'definition'
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

    def _get_answers(self, session_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT
                    questions.text AS question_text,
                    answers.text AS text
                FROM answers
                JOIN questions ON questions.id = answers.question_id
                WHERE questions.session_id = ?
                ORDER BY answers.id ASC
                """,
                (session_id,),
            ).fetchall()

    def _store_export_record(
        self,
        session_id: int,
        export_type: str,
        path: Path,
    ) -> ExportRecord:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO exports(session_id, export_type, path)
                VALUES (?, ?, ?)
                """,
                (session_id, export_type, str(path)),
            )
            connection.commit()
            export_id = int(cursor.lastrowid)

        return ExportRecord(
            id=export_id,
            session_id=session_id,
            export_type=export_type,
            path=str(path),
        )

    def _build_export_path(
        self,
        session_id: int,
        session_title: str,
        suffix: str,
        extension: str,
    ) -> Path:
        slug = slugify_filename(session_title)
        return self.config.export_dir / f"session_{session_id}_{slug}_{suffix}{extension}"


def extract_definition_term(text: str) -> str | None:
    match = re.match(
        r"^(.*?)(?:\bist\b|\bsind\b|\bmeans\b|\brefers to\b|\bbedeutet\b|\bheisst\b)",
        text,
        flags=re.IGNORECASE,
    )
    candidate = match.group(1).strip().rstrip(":,-") if match else ""
    return candidate or None


def slugify_filename(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "study_session"
