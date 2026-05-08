from pathlib import Path

from app.config import AppConfig
from app.db import Database
from app.schemas import TranscriptIngestRequest
from app.services.pipeline import TranscriptPipeline


def build_pipeline(tmp_path: Path) -> TranscriptPipeline:
    config = AppConfig(database_path=tmp_path / "test.db")
    database = Database(config.database_path)
    database.initialize()
    return TranscriptPipeline(database=database, config=config)


def test_ingest_persists_question(tmp_path: Path) -> None:
    pipeline = build_pipeline(tmp_path)
    session = pipeline.create_session("Storage")

    response = pipeline.ingest(
        TranscriptIngestRequest(
            session_id=session["id"],
            timestamp="00:35",
            language="de",
            text="Was ist RAID 1?",
            confidence=0.91,
            volume=0.4,
        )
    )

    assert response.accepted is True
    assert response.segment is not None
    assert response.segment.phrase_type == "question"
    assert len(pipeline.list_segments(session["id"])) == 1


def test_ingest_rejects_duplicates(tmp_path: Path) -> None:
    pipeline = build_pipeline(tmp_path)
    session = pipeline.create_session("Duplicates")
    payload = TranscriptIngestRequest(
        session_id=session["id"],
        timestamp="00:35",
        language="de",
        text="Heute sprechen wir uber RAID",
        confidence=0.91,
        volume=0.5,
    )

    first = pipeline.ingest(payload)
    second = pipeline.ingest(payload)

    assert first.accepted is True
    assert second.accepted is False
    assert second.reason == "duplicate"


def test_ingest_rejects_silence(tmp_path: Path) -> None:
    pipeline = build_pipeline(tmp_path)
    session = pipeline.create_session("Audio")

    response = pipeline.ingest(
        TranscriptIngestRequest(
            session_id=session["id"],
            timestamp="00:35",
            language="de",
            text="Kurzer Test",
            confidence=0.91,
            volume=0.0,
        )
    )

    assert response.accepted is False
    assert response.reason == "silence"
