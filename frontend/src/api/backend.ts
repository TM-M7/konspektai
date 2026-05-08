import type { IngestResponse, SessionResponse } from "../types";

const API_BASE = "http://127.0.0.1:8000";

export async function createSession(title: string): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error(`Session creation failed with status ${response.status}`);
  }

  return (await response.json()) as SessionResponse;
}

export async function ingestTranscript(input: {
  sessionId: number;
  timestamp: string;
  language: string;
  text: string;
  confidence: number;
}): Promise<IngestResponse> {
  const response = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: input.sessionId,
      timestamp: input.timestamp,
      language: input.language,
      text: input.text,
      confidence: input.confidence,
    }),
  });

  if (!response.ok) {
    throw new Error(`Ingest failed with status ${response.status}`);
  }

  return (await response.json()) as IngestResponse;
}

export function getBackendBaseUrl(): string {
  return API_BASE;
}
