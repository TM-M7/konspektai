export type PhraseType =
  | "normal"
  | "question"
  | "important"
  | "definition"
  | "deadline"
  | "task"
  | "example"
  | "exam_hint";

export type Priority = "low" | "medium" | "high";

export type EventType = "transcript_segment" | "ingest_rejected" | "ai_answer" | "status";

export interface SessionResponse {
  id: number;
  title: string;
}

export interface SessionSummary {
  id: number;
  title: string;
  created_at: string;
  segment_count: number;
  question_count: number;
  answer_count: number;
}

export interface TranscriptSegment {
  id: number;
  session_id: number;
  timestamp: string;
  language: string;
  text: string;
  confidence: number;
  phrase_type: PhraseType;
  priority: Priority;
  show_answer: boolean;
  question_id?: number | null;
}

export interface IngestResponse {
  accepted: boolean;
  reason: string | null;
  segment: TranscriptSegment | null;
}

export interface AudioChunkRecord {
  id: number;
  session_id: number;
  timestamp: string;
  duration_seconds: number;
  average_volume: number;
  peak_volume: number;
  source: "manual_simulated" | "browser_microphone" | "tauri_microphone";
  language_hint: string | null;
  simulated_text: string;
  detected_language: string | null;
  validation_status: string;
  transcript_segment_id?: number | null;
}

export interface AudioChunkIngestResponse {
  accepted: boolean;
  reason: string | null;
  audio_chunk: AudioChunkRecord | null;
  segment: TranscriptSegment | null;
}

export interface EventEnvelope {
  event_type: EventType;
  payload: unknown;
}

export interface RejectedEventPayload {
  session_id: number;
  reason: string | null;
  text: string;
}

export interface AIAnswerRecord {
  id: number;
  session_id: number;
  question_id: number;
  segment_id: number;
  question_text: string;
  language: string;
  text: string;
}

export interface FlashcardRecord {
  id: number;
  session_id: number;
  front_text: string;
  back_text: string;
}

export interface ExportRecord {
  id: number;
  session_id: number;
  export_type: string;
  path: string;
}

export interface StatusPayload {
  kind?: string;
  state?: string;
  session_id?: number;
  segment_id?: number;
  message?: string;
}
