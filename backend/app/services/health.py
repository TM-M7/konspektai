from __future__ import annotations

import importlib.util
import logging
import sqlite3
from pathlib import Path

from app.config import AppConfig
from app.schemas import HealthCheckItem, HealthStatus, StartupHealthResponse


logger = logging.getLogger(__name__)


class StartupHealthService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    async def run(self) -> StartupHealthResponse:
        checks = [
            self._check_workspace_dir(self.config.workspace_dir),
            self._check_workspace_dir(self.config.export_dir),
            self._check_sqlite(),
            self._check_runtime_mode(),
            self._check_runtime_dependencies(),
        ]
        overall_status = summarize_status(checks)
        return StartupHealthResponse(overall_status=overall_status, checks=checks)

    def _check_workspace_dir(self, path: Path) -> HealthCheckItem:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return HealthCheckItem(name=f"path:{path.name}", status="ok", message=f"Directory ready: {path}")
        except OSError as exc:
            logger.exception("Workspace directory check failed")
            return HealthCheckItem(name=f"path:{path.name}", status="error", message=f"Directory not available: {exc}")

    def _check_sqlite(self) -> HealthCheckItem:
        try:
            self.config.database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.config.database_path) as connection:
                connection.execute("SELECT 1")
            return HealthCheckItem(name="sqlite", status="ok", message=f"SQLite ready: {self.config.database_path}")
        except sqlite3.Error as exc:
            logger.exception("SQLite check failed")
            return HealthCheckItem(name="sqlite", status="error", message=f"SQLite failed: {exc}")

    def _check_runtime_mode(self) -> HealthCheckItem:
        return HealthCheckItem(
            name="runtime-mode",
            status="ok",
            message=f"Runtime mode: transcription={self.config.transcription_mode}, answers={self.config.answer_mode}",
        )

    def _check_runtime_dependencies(self) -> HealthCheckItem:
        details: list[str] = []
        status: HealthStatus = "ok"

        if self.config.transcription_mode == "whisper":
            installed = importlib.util.find_spec("faster_whisper") is not None
            details.append("faster-whisper installed" if installed else "faster-whisper missing")
            if not installed:
                status = "warning"

        if self.config.answer_mode == "ollama":
            details.append("Ollama runtime enabled")

        if not details:
            details.append("Stub runtime dependencies only")

        return HealthCheckItem(name="runtime-dependencies", status=status, message=", ".join(details))


def summarize_status(checks: list[HealthCheckItem]) -> str:
    if any(item.status == "error" for item in checks):
        return "error"
    if any(item.status == "warning" for item in checks):
        return "warning"
    return "ok"
