from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    app_name: str = "konspektai-backend"
    database_path: Path = Field(default=Path("data/konspektai.db"))
    workspace_dir: Path = Field(default=Path("data/workspace"))
    export_dir: Path = Field(default=Path("data/exports"))
    answer_mode: str = "stub"
    transcription_mode: str = "manual"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: float = 8.0
    whisper_model_size: str = "small"
    whisper_compute_type: str = "auto"
    audio_chunk_min_duration_seconds: float = 1.0
    audio_chunk_max_duration_seconds: float = 12.0
    low_volume_threshold: float = 0.02
    high_volume_threshold: float = 0.98
    min_confidence: float = 0.45
    duplicate_window_size: int = 5


def get_config() -> AppConfig:
    return AppConfig(
        answer_mode=os.getenv("KONSPEKTAI_ANSWER_MODE", "stub"),
        transcription_mode=os.getenv("KONSPEKTAI_TRANSCRIPTION_MODE", "manual"),
        ollama_base_url=os.getenv("KONSPEKTAI_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("KONSPEKTAI_OLLAMA_MODEL", "qwen2.5:7b"),
        ollama_timeout_seconds=float(os.getenv("KONSPEKTAI_OLLAMA_TIMEOUT_SECONDS", "8.0")),
        whisper_model_size=os.getenv("KONSPEKTAI_WHISPER_MODEL_SIZE", "small"),
        whisper_compute_type=os.getenv("KONSPEKTAI_WHISPER_COMPUTE_TYPE", "auto"),
    )
