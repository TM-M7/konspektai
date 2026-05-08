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

export type EventType = "transcript_segment" | "ingest_rejected" | "status";

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
