const ACTIVE_SESSION_KEY = "konspektai.activeSessionId";

export function readActiveSessionId(): number | null {
  if (typeof window === "undefined") {
    return null;
  }

  const rawValue = window.localStorage.getItem(ACTIVE_SESSION_KEY);
  if (!rawValue) {
    return null;
  }

  const sessionId = Number(rawValue);
  return Number.isInteger(sessionId) && sessionId > 0 ? sessionId : null;
}

export function writeActiveSessionId(sessionId: number | null): void {
  if (typeof window === "undefined") {
    return;
  }

  if (sessionId === null) {
    window.localStorage.removeItem(ACTIVE_SESSION_KEY);
    return;
  }

  window.localStorage.setItem(ACTIVE_SESSION_KEY, String(sessionId));
}
