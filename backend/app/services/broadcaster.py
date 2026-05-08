from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterable

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class EventBroadcaster:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("WebSocket client connected, total=%s", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("WebSocket client disconnected, total=%s", len(self._connections))

    async def broadcast(self, event: str, payload: dict) -> None:
        message = json.dumps({"event_type": event, "payload": payload})
        stale: list[WebSocket] = []
        for connection in await self._snapshot():
            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)
        if stale:
            await self._remove_many(stale)

    async def _snapshot(self) -> Iterable[WebSocket]:
        async with self._lock:
            return tuple(self._connections)

    async def _remove_many(self, stale: list[WebSocket]) -> None:
        async with self._lock:
            for connection in stale:
                self._connections.discard(connection)
