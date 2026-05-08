from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config
from app.db import Database
from app.logging_setup import configure_logging
from app.schemas import AIAnswerRecord, IngestResponse, SessionCreateRequest, SessionResponse, StartupHealthResponse, TranscriptIngestRequest, TranscriptSegment
from app.services.answering import AnswerGenerationError, QuestionAnswerService
from app.services.broadcaster import EventBroadcaster
from app.services.health import StartupHealthService
from app.services.pipeline import TranscriptPipeline


configure_logging()
logger = logging.getLogger(__name__)

config = get_config()
database = Database(config.database_path)
database.initialize()
broadcaster = EventBroadcaster()
pipeline = TranscriptPipeline(database=database, config=config)
answer_service = QuestionAnswerService(database=database, config=config)
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


@app.post("/ingest", response_model=IngestResponse)
async def ingest_segment(
    request: TranscriptIngestRequest,
    background_tasks: BackgroundTasks,
) -> IngestResponse:
    result = pipeline.ingest(request)
    if result.accepted and result.segment:
        await broadcaster.broadcast("transcript_segment", result.segment.model_dump())
        if result.segment.show_answer and result.segment.question_id is not None:
            background_tasks.add_task(process_question_answer, result.segment)
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


@app.get("/sessions/{session_id}/segments", response_model=list[TranscriptSegment])
async def list_segments(session_id: int) -> list[TranscriptSegment]:
    return pipeline.list_segments(session_id)


@app.get("/sessions/{session_id}/answers", response_model=list[AIAnswerRecord])
async def list_answers(session_id: int) -> list[AIAnswerRecord]:
    return answer_service.list_answers(session_id)


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


async def process_question_answer(segment: TranscriptSegment) -> None:
    await broadcaster.broadcast(
        "status",
        {
            "kind": "ai_answer",
            "state": "thinking",
            "session_id": segment.session_id,
            "segment_id": segment.id,
            "message": f"AI thinking about: {segment.text}",
        },
    )
    try:
        answer = await answer_service.generate_for_segment(segment)
    except AnswerGenerationError as exc:
        await broadcaster.broadcast(
            "status",
            {
                "kind": "ai_answer",
                "state": exc.reason,
                "session_id": segment.session_id,
                "segment_id": segment.id,
                "message": "AI answer not received",
            },
        )
        return

    await broadcaster.broadcast("ai_answer", answer.model_dump())
    await broadcaster.broadcast(
        "status",
        {
            "kind": "ai_answer",
            "state": "completed",
            "session_id": segment.session_id,
            "segment_id": segment.id,
            "message": "AI answer ready",
        },
    )
