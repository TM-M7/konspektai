from pathlib import Path

from fastapi.testclient import TestClient

from app.config import AppConfig
from app.db import Database
from app.main import app
from app.schemas import AudioChunkIngestRequest
from app.services.audio import AudioChunkService
from app.services.pipeline import TranscriptPipeline


def build_audio_service(tmp_path: Path) -> tuple[Database, AudioChunkService, TranscriptPipeline]:
    config = AppConfig(database_path=tmp_path / "audio.db")
    database = Database(config.database_path)
    database.initialize()
    pipeline = TranscriptPipeline(database=database, config=config)
    return database, AudioChunkService(database=database, pipeline=pipeline, config=config), pipeline


def test_audio_chunk_ingest_accepts_valid_simulated_chunk(tmp_path: Path) -> None:
    _, audio_service, pipeline = build_audio_service(tmp_path)
    session = pipeline.create_session("Audio Ready")

    response = audio_service.ingest_chunk(
        AudioChunkIngestRequest(
            session_id=session["id"],
            timestamp="00:42",
            duration_seconds=4.0,
            average_volume=0.44,
            peak_volume=0.62,
            source="manual_simulated",
            simulated_text="Was ist RAID 1?",
            language_hint="de",
        )
    )

    assert response.accepted is True
    assert response.segment is not None
    assert response.audio_chunk is not None
    assert response.audio_chunk.validation_status == "accepted"
    assert response.segment.phrase_type == "question"


def test_audio_chunk_ingest_rejects_silence(tmp_path: Path) -> None:
    _, audio_service, pipeline = build_audio_service(tmp_path)
    session = pipeline.create_session("Silent Audio")

    response = audio_service.ingest_chunk(
        AudioChunkIngestRequest(
            session_id=session["id"],
            timestamp="00:42",
            duration_seconds=4.0,
            average_volume=0.0,
            peak_volume=0.01,
            source="manual_simulated",
            simulated_text="Was ist RAID 1?",
            language_hint="de",
        )
    )

    assert response.accepted is False
    assert response.reason == "silence"
    assert response.audio_chunk is not None
    assert response.audio_chunk.validation_status == "silence"


def test_audio_chunk_requires_text_in_non_whisper_mode(tmp_path: Path) -> None:
    _, audio_service, pipeline = build_audio_service(tmp_path)
    session = pipeline.create_session("Audio Validation")

    response = audio_service.ingest_chunk(
        AudioChunkIngestRequest(
            session_id=session["id"],
            timestamp="00:42",
            duration_seconds=4.0,
            average_volume=0.44,
            peak_volume=0.62,
            source="manual_simulated",
            simulated_text="",
            language_hint="de",
        )
    )

    assert response.accepted is False
    assert response.reason == "empty_transcript"


def test_audio_chunk_api_round_trip() -> None:
    with TestClient(app) as client:
        session = client.post("/sessions", json={"title": "Audio API"}).json()
        response = client.post(
            "/audio/chunks",
            json={
                "session_id": session["id"],
                "timestamp": "00:42",
                "duration_seconds": 4.0,
                "average_volume": 0.44,
                "peak_volume": 0.62,
                "source": "manual_simulated",
                "simulated_text": "Was ist RAID 1?",
                "language_hint": "de",
            },
        )
        history = client.get(f"/sessions/{session['id']}/audio-chunks")

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert response.json()["segment"]["phrase_type"] == "question"
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_whisper_mode_requires_audio_payload(tmp_path: Path) -> None:
    config = AppConfig(database_path=tmp_path / "whisper.db", transcription_mode="whisper")
    database = Database(config.database_path)
    database.initialize()
    pipeline = TranscriptPipeline(database=database, config=config)
    audio_service = AudioChunkService(database=database, pipeline=pipeline, config=config)
    session = pipeline.create_session("Whisper Mode")

    try:
        audio_service.ingest_chunk(
            AudioChunkIngestRequest(
                session_id=session["id"],
                timestamp="00:42",
                duration_seconds=4.0,
                average_volume=0.44,
                peak_volume=0.62,
                source="manual_simulated",
                simulated_text="",
                language_hint="de",
            )
        )
    except ValueError as exc:
        assert str(exc) == "audio_base64_required"
    else:
        raise AssertionError("Expected whisper mode to require audio payload")


def test_audio_chunk_api_accepts_browser_microphone_source() -> None:
    with TestClient(app) as client:
        session = client.post("/sessions", json={"title": "Browser Audio"}).json()
        response = client.post(
            "/audio/chunks",
            json={
                "session_id": session["id"],
                "timestamp": "00:55",
                "duration_seconds": 4.1,
                "average_volume": 0.38,
                "peak_volume": 0.57,
                "source": "browser_microphone",
                "simulated_text": "Heute sprechen wir uber RAID.",
                "language_hint": "de",
            },
        )

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert response.json()["audio_chunk"]["source"] == "browser_microphone"
