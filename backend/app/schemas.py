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
AudioSource = Literal["manual_simulated", "browser_microphone", "tauri_microphone"]
AudioValidationStatus = Literal["accepted", "silence", "too_loud", "invalid_duration", "empty_transcript"]


class HealthCheckItem(BaseModel):
    name: str
    status: HealthStatus
    message: str


class StartupHealthResponse(BaseModel):
    overall_status: HealthStatus
    checks: list[HealthCheckItem]


class SessionCreateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"title": "Test lesson"}})
    title: str = Field(min_length=1, max_length=200)


class SessionResponse(BaseModel):
    id: int
    title: str


class SessionSummary(BaseModel):
    id: int
    title: str
    created_at: str
    segment_count: int
    question_count: int
    answer_count: int


class SessionUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


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


class AudioChunkIngestRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": 1,
                "timestamp": "00:42",
                "duration_seconds": 4.0,
                "average_volume": 0.44,
                "peak_volume": 0.62,
                "source": "manual_simulated",
                "simulated_text": "Was ist RAID 1?",
                "language_hint": "de",
                "audio_base64": None,
                "audio_format": None,
            }
        }
    )
    session_id: int
    timestamp: str = Field(min_length=1, max_length=20)
    duration_seconds: float = Field(gt=0.0, le=120.0)
    average_volume: float = Field(ge=0.0, le=1.0)
    peak_volume: float = Field(ge=0.0, le=1.0)
    source: AudioSource = "manual_simulated"
    simulated_text: str = Field(default="", max_length=5000)
    language_hint: str | None = Field(default=None, max_length=8)
    audio_base64: str | None = None
    audio_format: str | None = Field(default=None, max_length=16)


class AudioChunkRecord(BaseModel):
    id: int
    session_id: int
    timestamp: str
    duration_seconds: float
    average_volume: float
    peak_volume: float
    source: AudioSource
    language_hint: str | None
    simulated_text: str
    detected_language: str | None
    validation_status: AudioValidationStatus
    transcript_segment_id: int | None = None


class AudioChunkIngestResponse(BaseModel):
    accepted: bool
    reason: str | None = None
    audio_chunk: AudioChunkRecord | None = None
    segment: TranscriptSegment | None = None


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


class FlashcardRecord(BaseModel):
    id: int
    session_id: int
    front_text: str
    back_text: str


class ExportRecord(BaseModel):
    id: int
    session_id: int
    export_type: str
    path: str


class EventEnvelope(BaseModel):
    event_type: Literal["transcript_segment", "ingest_rejected", "ai_answer", "status"]
    payload: dict
