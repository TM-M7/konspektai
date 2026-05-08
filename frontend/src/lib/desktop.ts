declare global {
  interface Window {
    __TAURI__?: unknown;
    __TAURI_INTERNALS__?: unknown;
  }
}

export function isDesktopShellAvailable(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  return Boolean(window.__TAURI__ || window.__TAURI_INTERNALS__);
}

export function getRuntimeLabel(): string {
  return isDesktopShellAvailable() ? "desktop shell detected" : "browser dev mode";
}
