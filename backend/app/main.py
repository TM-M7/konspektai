from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config
from app.db import Database
from app.logging_setup import configure_logging
from app.schemas import AIAnswerRecord, AudioChunkIngestRequest, AudioChunkIngestResponse, AudioChunkRecord, ExportRecord, FlashcardRecord, IngestResponse, SessionCreateRequest, SessionResponse, SessionSummary, SessionUpdateRequest, StartupHealthResponse, TranscriptIngestRequest, TranscriptSegment
from app.services.answering import AnswerGenerationError, QuestionAnswerService
from app.services.audio import AudioChunkService
from app.services.broadcaster import EventBroadcaster
from app.services.health import StartupHealthService
from app.services.materials import StudyMaterialsService
from app.services.pipeline import TranscriptPipeline


configure_logging()
logger = logging.getLogger(__name__)

config = get_config()
database = Database(config.database_path)
database.initialize()
broadcaster = EventBroadcaster()
pipeline = TranscriptPipeline(database=database, config=config)
audio_service = AudioChunkService(database=database, pipeline=pipeline, config=config)
answer_service = QuestionAnswerService(database=database, config=config)
materials_service = StudyMaterialsService(database=database, config=config)
health_service = StartupHealthService(config=config)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Initializing database")
    database.initialize()
    yield


app = FastAPI(title="konspektai backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/startup", response_model=StartupHealthResponse)
async def startup_health() -> StartupHealthResponse:
    return await health_service.run()


@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest) -> SessionResponse:
    session = pipeline.create_session(request.title)
    return SessionResponse(**session)


@app.get("/sessions", response_model=list[SessionSummary])
async def list_sessions() -> list[SessionSummary]:
    return pipeline.list_sessions()


@app.get("/sessions/{session_id}", response_model=SessionSummary)
async def get_session(session_id: int) -> SessionSummary:
    session = pipeline.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return session


@app.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: int, request: SessionUpdateRequest) -> SessionResponse:
    session = pipeline.update_session_title(session_id, request.title)
    if session is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return SessionResponse(**session)


@app.post("/ingest", response_model=IngestResponse)
async def ingest_segment(request: TranscriptIngestRequest) -> IngestResponse:
    result = pipeline.ingest(request)
    if result.accepted and result.segment:
        await broadcaster.broadcast("transcript_segment", result.segment.model_dump())
    else:
        await broadcaster.broadcast(
            "ingest_rejected",
            {
                "session_id": request.session_id,
                "reason": result.reason,
                "text": request.text,
            },
        )
    return result


@app.post("/audio/chunks", response_model=AudioChunkIngestResponse)
async def ingest_audio_chunk(request: AudioChunkIngestRequest) -> AudioChunkIngestResponse:
    try:
        result = audio_service.ingest_chunk(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result.accepted and result.segment:
        await broadcaster.broadcast("transcript_segment", result.segment.model_dump())
    return result


@app.get("/sessions/{session_id}/segments", response_model=list[TranscriptSegment])
async def list_segments(session_id: int) -> list[TranscriptSegment]:
    return pipeline.list_segments(session_id)


@app.get("/sessions/{session_id}/audio-chunks", response_model=list[AudioChunkRecord])
async def list_audio_chunks(session_id: int) -> list[AudioChunkRecord]:
    return audio_service.list_chunks(session_id)


@app.get("/sessions/{session_id}/answers", response_model=list[AIAnswerRecord])
async def list_answers(session_id: int) -> list[AIAnswerRecord]:
    return answer_service.list_answers(session_id)


@app.post("/questions/{question_id}/answer", response_model=AIAnswerRecord)
async def generate_question_answer(question_id: int) -> AIAnswerRecord:
    try:
        return await answer_service.generate_for_question_id(question_id)
    except AnswerGenerationError as exc:
        if exc.reason == "unknown_question":
            raise HTTPException(status_code=404, detail="question_not_found") from exc
        raise HTTPException(status_code=400, detail=exc.reason) from exc


@app.post("/sessions/{session_id}/flashcards/generate", response_model=list[FlashcardRecord])
async def generate_flashcards(session_id: int) -> list[FlashcardRecord]:
    try:
        return materials_service.generate_flashcards(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="session_not_found") from exc


@app.get("/sessions/{session_id}/flashcards", response_model=list[FlashcardRecord])
async def list_flashcards(session_id: int) -> list[FlashcardRecord]:
    return materials_service.list_flashcards(session_id)


@app.post("/sessions/{session_id}/export/markdown", response_model=ExportRecord)
async def export_markdown(session_id: int) -> ExportRecord:
    try:
        return materials_service.export_markdown(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="session_not_found") from exc


@app.post("/sessions/{session_id}/export/anki_csv", response_model=ExportRecord)
async def export_anki_csv(session_id: int) -> ExportRecord:
    try:
        return materials_service.export_anki_csv(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="session_not_found") from exc


@app.get("/sessions/{session_id}/exports", response_model=list[ExportRecord])
async def list_exports(session_id: int) -> list[ExportRecord]:
    return materials_service.list_exports(session_id)


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    await broadcaster.connect(websocket)
    await broadcaster.broadcast(
        "status",
        {
            "message": "WebSocket client connected",
        },
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect(websocket)
