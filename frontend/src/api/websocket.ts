import type { EventEnvelope } from "../types";

const WS_URL = "ws://127.0.0.1:8000/ws/events";

export function connectEvents(onEvent: (event: EventEnvelope) => void): WebSocket {
  const socket = new WebSocket(WS_URL);

  socket.onmessage = (message) => {
    const parsed = JSON.parse(message.data) as EventEnvelope;
    onEvent(parsed);
  };

  return socket;
}

export function getWebSocketUrl(): string {
  return WS_URL;
}
