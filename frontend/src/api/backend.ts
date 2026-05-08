import type {
  AIAnswerRecord,
  AudioChunkIngestResponse,
  AudioChunkRecord,
  ExportRecord,
  FlashcardRecord,
  IngestResponse,
  SessionResponse,
  SessionSummary,
  TranscriptSegment,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function expectJson<T>(response: Response, errorMessage: string): Promise<T> {
  if (!response.ok) {
    throw new Error(`${errorMessage} (${response.status})`);
  }

  return (await response.json()) as T;
}

export async function createSession(title: string): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });

  return expectJson<SessionResponse>(response, "Session creation failed");
}

export async function listSessions(): Promise<SessionSummary[]> {
  const response = await fetch(`${API_BASE}/sessions`);
  return expectJson<SessionSummary[]>(response, "Session list request failed");
}

export async function getSession(sessionId: number): Promise<SessionSummary> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`);
  return expectJson<SessionSummary>(response, "Session fetch failed");
}

export async function renameSession(sessionId: number, title: string): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });

  return expectJson<SessionResponse>(response, "Session rename failed");
}

export async function listSegments(sessionId: number): Promise<TranscriptSegment[]> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/segments`);
  return expectJson<TranscriptSegment[]>(response, "Segment list request failed");
}

export async function listAnswers(sessionId: number): Promise<AIAnswerRecord[]> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/answers`);
  return expectJson<AIAnswerRecord[]>(response, "Answer list request failed");
}

export async function listAudioChunks(sessionId: number): Promise<AudioChunkRecord[]> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/audio-chunks`);
  return expectJson<AudioChunkRecord[]>(response, "Audio chunk list request failed");
}

export async function listFlashcards(sessionId: number): Promise<FlashcardRecord[]> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/flashcards`);
  return expectJson<FlashcardRecord[]>(response, "Flashcard list request failed");
}

export async function listExports(sessionId: number): Promise<ExportRecord[]> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/exports`);
  return expectJson<ExportRecord[]>(response, "Export list request failed");
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

  return expectJson<IngestResponse>(response, "Ingest failed");
}

export async function ingestAudioChunk(input: {
  sessionId: number;
  timestamp: string;
  durationSeconds: number;
  averageVolume: number;
  peakVolume: number;
  simulatedText: string;
  languageHint: string;
  source?: "manual_simulated" | "browser_microphone" | "tauri_microphone";
  audioBase64?: string | null;
  audioFormat?: string | null;
}): Promise<AudioChunkIngestResponse> {
  const response = await fetch(`${API_BASE}/audio/chunks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: input.sessionId,
      timestamp: input.timestamp,
      duration_seconds: input.durationSeconds,
      average_volume: input.averageVolume,
      peak_volume: input.peakVolume,
      source: input.source ?? "manual_simulated",
      simulated_text: input.simulatedText,
      language_hint: input.languageHint,
      audio_base64: input.audioBase64 ?? null,
      audio_format: input.audioFormat ?? null,
    }),
  });

  return expectJson<AudioChunkIngestResponse>(response, "Audio chunk ingest failed");
}

export async function generateAnswer(questionId: number): Promise<AIAnswerRecord> {
  const response = await fetch(`${API_BASE}/questions/${questionId}/answer`, {
    method: "POST",
  });

  return expectJson<AIAnswerRecord>(response, "Answer generation failed");
}

export async function generateFlashcards(sessionId: number): Promise<FlashcardRecord[]> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/flashcards/generate`, {
    method: "POST",
  });

  return expectJson<FlashcardRecord[]>(response, "Flashcard generation failed");
}

export async function exportMarkdown(sessionId: number): Promise<ExportRecord> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/export/markdown`, {
    method: "POST",
  });

  return expectJson<ExportRecord>(response, "Markdown export failed");
}

export async function exportAnkiCsv(sessionId: number): Promise<ExportRecord> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/export/anki_csv`, {
    method: "POST",
  });

  return expectJson<ExportRecord>(response, "Anki CSV export failed");
}

export function getBackendBaseUrl(): string {
  return API_BASE;
}
