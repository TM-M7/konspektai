from __future__ import annotations

import importlib
import importlib.util
import logging
import sqlite3
from pathlib import Path

import httpx

from app.config import AppConfig
from app.schemas import HealthCheckItem, StartupHealthResponse


logger = logging.getLogger(__name__)


class StartupHealthService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    async def run(self) -> StartupHealthResponse:
        checks = [
            self._check_workspace_dir(self.config.workspace_dir),
            self._check_workspace_dir(self.config.export_dir),
            self._check_sqlite(),
            self._check_python_package("faster_whisper", "faster-whisper"),
            self._check_microphone(),
            await self._check_ollama(),
            await self._check_ollama_model(),
        ]
        overall_status = summarize_status(checks)
        return StartupHealthResponse(overall_status=overall_status, checks=checks)

    def _check_workspace_dir(self, path: Path) -> HealthCheckItem:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return HealthCheckItem(
                name=f"path:{path.name}",
                status="ok",
                message=f"Directory ready: {path}",
            )
        except OSError as exc:
            logger.exception("Workspace directory check failed")
            return HealthCheckItem(
                name=f"path:{path.name}",
                status="error",
                message=f"Directory not available: {exc}",
            )

    def _check_sqlite(self) -> HealthCheckItem:
        try:
            self.config.database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.config.database_path) as connection:
                connection.execute("SELECT 1")
            return HealthCheckItem(
                name="sqlite",
                status="ok",
                message=f"SQLite ready: {self.config.database_path}",
            )
        except sqlite3.Error as exc:
            logger.exception("SQLite check failed")
            return HealthCheckItem(
                name="sqlite",
                status="error",
                message=f"SQLite failed: {exc}",
            )

    def _check_python_package(self, module_name: str, label: str) -> HealthCheckItem:
        if importlib.util.find_spec(module_name):
            return HealthCheckItem(
                name=label,
                status="ok",
                message=f"{label} is installed",
            )
        return HealthCheckItem(
            name=label,
            status="warning",
            message=f"{label} is not installed",
        )

    def _check_microphone(self) -> HealthCheckItem:
        if not importlib.util.find_spec("sounddevice"):
            return HealthCheckItem(
                name="microphone",
                status="warning",
                message="sounddevice is not installed",
            )

        try:
            sounddevice = importlib.import_module("sounddevice")
            devices = sounddevice.query_devices()
            input_devices = [device for device in devices if device.get("max_input_channels", 0) > 0]
            if input_devices:
                return HealthCheckItem(
                    name="microphone",
                    status="ok",
                    message=f"Input devices found: {len(input_devices)}",
                )
            return HealthCheckItem(
                name="microphone",
                status="warning",
                message="No microphone input devices found",
            )
        except Exception as exc:
            logger.exception("Microphone check failed")
            return HealthCheckItem(
                name="microphone",
                status="warning",
                message=f"Microphone check failed: {exc}",
            )

    async def _check_ollama(self) -> HealthCheckItem:
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.get(f"{self.config.ollama_base_url}/api/tags")
                response.raise_for_status()
            return HealthCheckItem(
                name="ollama",
                status="ok",
                message="Ollama is reachable",
            )
        except httpx.HTTPError as exc:
            return HealthCheckItem(
                name="ollama",
                status="warning",
                message=f"Ollama is not reachable: {exc}",
            )

    async def _check_ollama_model(self) -> HealthCheckItem:
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.get(f"{self.config.ollama_base_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            return HealthCheckItem(
                name="ollama-model",
                status="warning",
                message=f"Model check skipped because Ollama is unavailable: {exc}",
            )

        models = [item.get("name", "") for item in payload.get("models", [])]
        if self.config.ollama_model in models:
            return HealthCheckItem(
                name="ollama-model",
                status="ok",
                message=f"Model ready: {self.config.ollama_model}",
            )
        return HealthCheckItem(
            name="ollama-model",
            status="warning",
            message=f"Model missing: run `ollama pull {self.config.ollama_model}`",
        )


def summarize_status(checks: list[HealthCheckItem]) -> str:
    if any(item.status == "error" for item in checks):
        return "error"
    if any(item.status == "warning" for item in checks):
        return "warning"
    return "ok"
