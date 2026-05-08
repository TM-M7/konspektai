import { useEffect, useState, type FormEvent } from "react";

import type { SessionResponse, SessionSummary } from "../types";

interface SessionControlsProps {
  currentSession: SessionResponse | null;
  sessions: SessionSummary[];
  onCreateSession: (title: string) => Promise<void>;
  onRenameSession: (title: string) => Promise<void>;
  onResumeSession: (sessionId: number) => Promise<void>;
  isBusy: boolean;
  isLoadingSessions: boolean;
}

export function SessionControls({
  currentSession,
  sessions,
  onCreateSession,
  onRenameSession,
  onResumeSession,
  isBusy,
  isLoadingSessions,
}: SessionControlsProps) {
  const [createTitle, setCreateTitle] = useState("Test lesson");
  const [renameTitle, setRenameTitle] = useState("");

  useEffect(() => {
    setRenameTitle(currentSession?.title ?? "");
  }, [currentSession]);

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCreateSession(createTitle);
  }

  async function handleRenameSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!currentSession) {
      return;
    }

    await onRenameSession(renameTitle);
  }

  return (
    <section className="panel session-panel">
      <div className="session-panel-header">
        <div>
          <h2>Session Control</h2>
          <div className="session-meta">
            <div>Current session: {currentSession ? currentSession.title : "none"}</div>
            <div>Session id: {currentSession ? currentSession.id : "-"}</div>
          </div>
        </div>
        <div className="session-chip">{isLoadingSessions ? "Syncing sessions" : `${sessions.length} saved`}</div>
      </div>

      <div className="session-layout">
        <form className="session-form" onSubmit={handleCreateSubmit}>
          <h3>Start New Session</h3>
          <label>
            Title
            <input
              value={createTitle}
              onChange={(event) => setCreateTitle(event.target.value)}
              placeholder="Test lesson"
            />
          </label>
          <button disabled={isBusy} type="submit">
            {isBusy ? "Creating..." : "Start Session"}
          </button>
        </form>

        <form className="session-form" onSubmit={handleRenameSubmit}>
          <h3>Rename Current Session</h3>
          <label>
            Title
            <input
              disabled={!currentSession}
              value={renameTitle}
              onChange={(event) => setRenameTitle(event.target.value)}
              placeholder="Rename current session"
            />
          </label>
          <button disabled={!currentSession || isBusy} type="submit">
            {isBusy ? "Saving..." : "Save Title"}
          </button>
        </form>

        <div className="session-form">
          <h3>Recent Sessions</h3>
          {sessions.length === 0 ? (
            <div className="muted">No saved sessions yet.</div>
          ) : (
            sessions.slice(0, 6).map((session) => (
              <button
                key={session.id}
                className="secondary-button session-list-button"
                disabled={isBusy}
                onClick={() => void onResumeSession(session.id)}
                type="button"
              >
                <strong>{session.title}</strong>
                <span>
                  #{session.id} · {session.segment_count} segments · {session.question_count} questions
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
