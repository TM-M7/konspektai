from pathlib import Path

from app.config import AppConfig
from app.db import Database
from app.services.materials import StudyMaterialsService, slugify_filename


def build_materials_service(tmp_path: Path) -> tuple[Database, StudyMaterialsService]:
    config = AppConfig(
        database_path=tmp_path / "materials.db",
        export_dir=tmp_path / "exports",
    )
    database = Database(config.database_path)
    database.initialize()
    return database, StudyMaterialsService(database=database, config=config)


def seed_session_data(database: Database) -> int:
    with database.connect() as connection:
        session_cursor = connection.execute(
            "INSERT INTO sessions(title) VALUES (?)",
            ("Materials Test",),
        )
        session_id = int(session_cursor.lastrowid)
        segment_cursor = connection.execute(
            """
            INSERT INTO transcript_segments(
                session_id, ts, language, text, confidence, phrase_type, priority, show_answer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                "00:35",
                "de",
                "RAID 1 ist eine Spiegelung von Daten.",
                0.95,
                "definition",
                "medium",
                0,
            ),
        )
        question_segment_id = int(segment_cursor.lastrowid)
        question_cursor = connection.execute(
            "INSERT INTO questions(session_id, segment_id, text) VALUES (?, ?, ?)",
            (session_id, question_segment_id, "Was ist RAID 1?"),
        )
        question_id = int(question_cursor.lastrowid)
        connection.execute(
            "INSERT INTO answers(question_id, language, text) VALUES (?, ?, ?)",
            (
                question_id,
                "de",
                "RAID 1 spiegelt Daten auf zwei Festplatten. RU: RAID 1 зеркалирует данные.",
            ),
        )
        connection.commit()
    return session_id


def test_generate_flashcards_creates_cards_from_answers_and_definitions(tmp_path: Path) -> None:
    database, materials = build_materials_service(tmp_path)
    session_id = seed_session_data(database)

    cards = materials.generate_flashcards(session_id)

    assert len(cards) == 2
    assert cards[0].front_text == "Was ist RAID 1?"
    assert "RAID 1 ist eine Spiegelung" in cards[1].back_text


def test_export_markdown_and_anki_csv_create_files(tmp_path: Path) -> None:
    database, materials = build_materials_service(tmp_path)
    session_id = seed_session_data(database)
    materials.generate_flashcards(session_id)

    markdown_export = materials.export_markdown(session_id)
    anki_export = materials.export_anki_csv(session_id)

    assert Path(markdown_export.path).exists()
    assert Path(anki_export.path).exists()
    assert Path(markdown_export.path).read_text(encoding="utf-8").startswith("# Materials Test")
    assert "What is RAID 1?" in Path(anki_export.path).read_text(encoding="utf-8")
    assert markdown_export.path.endswith("session_1_materials_test_notes.md")
    assert anki_export.path.endswith("session_1_materials_test_anki.csv")


def test_generate_flashcards_for_unknown_session_raises_value_error(tmp_path: Path) -> None:
    _, materials = build_materials_service(tmp_path)

    try:
        materials.generate_flashcards(999)
    except ValueError as exc:
        assert "Unknown session" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown session")


def test_slugify_filename_is_safe() -> None:
    assert slugify_filename(" Netzwerke / RAID: Prüfung! ") == "netzwerke_raid_pr_fung"
