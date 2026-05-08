from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    app_name: str = "konspektai-backend"
    database_path: Path = Field(default=Path("data/konspektai.db"))
    workspace_dir: Path = Field(default=Path("data/workspace"))
    export_dir: Path = Field(default=Path("data/exports"))
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: float = 8.0
    low_volume_threshold: float = 0.02
    high_volume_threshold: float = 0.98
    min_confidence: float = 0.45
    duplicate_window_size: int = 5


def get_config() -> AppConfig:
    return AppConfig()
