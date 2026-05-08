import { useState, type FormEvent } from "react";

import type { SessionResponse } from "../types";

interface SessionControlsProps {
  currentSession: SessionResponse | null;
  onCreateSession: (title: string) => Promise<void>;
  isBusy: boolean;
}

export function SessionControls({
  currentSession,
  onCreateSession,
  isBusy,
}: SessionControlsProps) {
  const [title, setTitle] = useState("Test lesson");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCreateSession(title);
  }

  return (
    <section className="panel">
      <h2>Session</h2>
      <form className="session-form" onSubmit={handleSubmit}>
        <label>
          Title
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Test lesson"
          />
        </label>
        <button disabled={isBusy} type="submit">
          {isBusy ? "Creating..." : "Start Session"}
        </button>
      </form>
      <div className="session-meta">
        <div>Current session: {currentSession ? currentSession.title : "none"}</div>
        <div>Session id: {currentSession ? currentSession.id : "-"}</div>
      </div>
    </section>
  );
}
