from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config
from app.db import Database
from app.logging_setup import configure_logging
from app.schemas import IngestResponse, SessionCreateRequest, SessionResponse, StartupHealthResponse, TranscriptIngestRequest, TranscriptSegment
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


@app.get("/sessions/{session_id}/segments", response_model=list[TranscriptSegment])
async def list_segments(session_id: int) -> list[TranscriptSegment]:
    return pipeline.list_segments(session_id)


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
