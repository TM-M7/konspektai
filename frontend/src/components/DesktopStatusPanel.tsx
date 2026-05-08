import { getRuntimeLabel, isDesktopShellAvailable } from "../lib/desktop";

interface DesktopStatusPanelProps {
  currentSessionTitle: string | null;
}

export function DesktopStatusPanel({ currentSessionTitle }: DesktopStatusPanelProps) {
  const desktopMode = isDesktopShellAvailable();

  return (
    <section className="panel">
      <h2>0.8 Desktop Readiness</h2>
      <div className="desktop-status-grid">
        <div className="summary-card">
          <span className="summary-value">{desktopMode ? "Tauri" : "Browser"}</span>
          <span className="summary-label">{getRuntimeLabel()}</span>
        </div>
        <div className="summary-card">
          <span className="summary-value">{currentSessionTitle ? "Linked" : "Idle"}</span>
          <span className="summary-label">
            {currentSessionTitle ? `Session: ${currentSessionTitle}` : "No active session"}
          </span>
        </div>
      </div>
      <div className="muted">
        Tray and local packaging configs are prepared in <code>src-tauri/</code>. Build verification
        still depends on installing Rust and the Tauri CLI on this machine.
      </div>
    </section>
  );
}
