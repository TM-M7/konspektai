from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PhraseType = Literal[
    "normal",
    "question",
    "important",
    "definition",
    "deadline",
    "task",
    "example",
    "exam_hint",
]

Priority = Literal["low", "medium", "high"]
HealthStatus = Literal["ok", "warning", "error"]


class HealthCheckItem(BaseModel):
    name: str
    status: HealthStatus
    message: str


class StartupHealthResponse(BaseModel):
    overall_status: HealthStatus
    checks: list[HealthCheckItem]


class SessionCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Test lesson",
            }
        }
    )

    title: str = Field(min_length=1, max_length=200)


class SessionResponse(BaseModel):
    id: int
    title: str


class TranscriptIngestRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": 1,
                "timestamp": "00:35",
                "language": "de",
                "text": "Was ist der Unterschied zwischen RAID 0 und RAID 1?",
                "confidence": 0.91,
                "volume": 0.42,
            }
        }
    )

    session_id: int
    timestamp: str = Field(min_length=1, max_length=20)
    language: str = Field(min_length=2, max_length=8)
    text: str = Field(max_length=5000)
    confidence: float = Field(ge=0.0, le=1.0)
    volume: float | None = Field(default=None, ge=0.0, le=1.0)


class TranscriptSegment(BaseModel):
    id: int
    session_id: int
    timestamp: str
    language: str
    text: str
    confidence: float
    phrase_type: PhraseType
    priority: Priority
    show_answer: bool
    question_id: int | None = None


class IngestResponse(BaseModel):
    accepted: bool
    reason: str | None = None
    segment: TranscriptSegment | None = None


class PhraseClassification(BaseModel):
    phrase_type: PhraseType
    priority: Priority
    show_answer: bool


class AIAnswerRecord(BaseModel):
    id: int
    session_id: int
    question_id: int
    segment_id: int
    question_text: str
    language: str
    text: str


class EventEnvelope(BaseModel):
    event_type: Literal["transcript_segment", "ingest_rejected", "ai_answer", "status"]
    payload: dict
