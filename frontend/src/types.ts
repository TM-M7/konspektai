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

export interface StatusPayload {
  kind?: string;
  state?: string;
  session_id?: number;
  segment_id?: number;
  message?: string;
}
