import { useEffect, useState } from "react";

import { createSession, getBackendBaseUrl, ingestTranscript } from "./api/backend";
import { connectEvents, getWebSocketUrl } from "./api/websocket";
import { EventLog } from "./components/EventLog";
import { NotesPanel } from "./components/NotesPanel";
import { SessionControls } from "./components/SessionControls";
import { SubtitleOverlay } from "./components/SubtitleOverlay";
import { TextIngestBox } from "./components/TextIngestBox";
import type {
  EventEnvelope,
  RejectedEventPayload,
  SessionResponse,
  TranscriptSegment,
} from "./types";

function isObjectPayload(payload: unknown): payload is Record<string, unknown> {
  return typeof payload === "object" && payload !== null;
}

function isTranscriptSegment(payload: unknown): payload is TranscriptSegment {
  if (!isObjectPayload(payload)) {
    return false;
  }

  return (
    typeof payload.id === "number" &&
    typeof payload.session_id === "number" &&
    typeof payload.text === "string" &&
    typeof payload.timestamp === "string"
  );
}

function isRejectedPayload(payload: unknown): payload is RejectedEventPayload {
  if (!isObjectPayload(payload)) {
    return false;
  }

  return (
    typeof payload.session_id === "number" &&
    typeof payload.text === "string"
  );
}

export default function App() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [rejections, setRejections] = useState<string[]>([]);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [sessionBusy, setSessionBusy] = useState(false);
  const [requestBusy, setRequestBusy] = useState(false);
  const [uiError, setUiError] = useState<string | null>(null);

  useEffect(() => {
    const socket = connectEvents((event: EventEnvelope) => {
      if (event.event_type === "transcript_segment" && isTranscriptSegment(event.payload)) {
        const segment = event.payload;
        setSegments((current) => [...current, segment]);
        return;
      }

      if (event.event_type === "ingest_rejected" && isRejectedPayload(event.payload)) {
        const rejection = event.payload;
        setRejections((current) => [
          `Rejected: ${rejection.reason ?? "unknown"} - ${rejection.text}`,
          ...current,
        ]);
        return;
      }

      if (event.event_type === "status") {
        const message =
          isObjectPayload(event.payload) && typeof event.payload.message === "string"
            ? event.payload.message
            : "Connected";
        setStatusMessages((current) => [message, ...current]);
      }
    });

    socket.onerror = () => {
      setUiError("WebSocket connection failed. Start backend on http://127.0.0.1:8000.");
    };

    socket.onopen = () => {
      setStatusMessages((current) => [`WebSocket connected to ${getWebSocketUrl()}`, ...current]);
    };

    socket.onclose = () => {
      setStatusMessages((current) => ["WebSocket disconnected", ...current]);
    };

    return () => {
      socket.close();
    };
  }, []);

  async function handleCreateSession(title: string) {
    setUiError(null);
    setSessionBusy(true);
    try {
      const created = await createSession(title);
      setSession(created);
      setSegments([]);
      setRejections([]);
      setStatusMessages((current) => [
        `Session created: ${created.title} (#${created.id})`,
        ...current,
      ]);
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Session creation failed");
    } finally {
      setSessionBusy(false);
    }
  }

  async function handleSend(payload: {
    timestamp: string;
    language: string;
    text: string;
    confidence: number;
  }) {
    if (!session) {
      setUiError("Create a session before sending transcript text.");
      return;
    }

    setUiError(null);
    setRequestBusy(true);
    try {
      await ingestTranscript({
        sessionId: session.id,
        timestamp: payload.timestamp,
        language: payload.language,
        text: payload.text,
        confidence: payload.confidence,
      });
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Ingest failed");
    } finally {
      setRequestBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <SubtitleOverlay segments={segments} />

      <div className="workspace">
        <NotesPanel segments={segments} />

        <section className="main-column">
          <header className="hero panel">
            <h1>konspektai 0.2 text mode</h1>
            <p>
              Manual transcript test mode for proving realtime backend to frontend flow.
            </p>
            <div className="endpoint-list">
              <span>API: {getBackendBaseUrl()}</span>
              <span>WS: {getWebSocketUrl()}</span>
            </div>
            {uiError ? <div className="error-banner">{uiError}</div> : null}
          </header>

          <SessionControls
            currentSession={session}
            isBusy={sessionBusy}
            onCreateSession={handleCreateSession}
          />

          <TextIngestBox disabled={!session || requestBusy} onSend={handleSend} />

          <EventLog
            segments={segments}
            rejections={rejections}
            statusMessages={statusMessages}
          />
        </section>
      </div>
    </main>
  );
}
