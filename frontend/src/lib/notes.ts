import type { TranscriptSegment } from "../types";

export interface NotesBuckets {
  notes: TranscriptSegment[];
  questions: TranscriptSegment[];
  important: TranscriptSegment[];
  deadlines: TranscriptSegment[];
  tasks: TranscriptSegment[];
  definitions: TranscriptSegment[];
  examHints: TranscriptSegment[];
  examples: TranscriptSegment[];
  terms: string[];
}

export function buildNotesBuckets(segments: TranscriptSegment[]): NotesBuckets {
  const uniqueSegments = uniqueByTypeAndText(segments);
  const definitions = uniqueSegments.filter((segment) => segment.phrase_type === "definition");

  return {
    notes: uniqueSegments.filter((segment) => segment.phrase_type === "normal"),
    questions: uniqueSegments.filter((segment) => segment.phrase_type === "question"),
    important: uniqueSegments.filter((segment) => segment.phrase_type === "important"),
    deadlines: uniqueSegments.filter((segment) => segment.phrase_type === "deadline"),
    tasks: uniqueSegments.filter((segment) => segment.phrase_type === "task"),
    definitions,
    examHints: uniqueSegments.filter((segment) => segment.phrase_type === "exam_hint"),
    examples: uniqueSegments.filter((segment) => segment.phrase_type === "example"),
    terms: extractTerms(definitions),
  };
}

function uniqueByTypeAndText(segments: TranscriptSegment[]): TranscriptSegment[] {
  const seen = new Set<string>();
  return segments.filter((segment) => {
    const key = `${segment.phrase_type}:${segment.text.trim().toLowerCase()}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function extractTerms(definitions: TranscriptSegment[]): string[] {
  const seen = new Set<string>();
  const terms: string[] = [];

  for (const segment of definitions) {
    const match = segment.text.match(
      /^(.*?)(?:\bist\b|\bsind\b|\bmeans\b|\brefers to\b|\bbedeutet\b|\bheisst\b)/i,
    );
    const candidate = match?.[1]?.trim().replace(/[:,-]+$/, "");

    if (!candidate) {
      continue;
    }

    const normalized = candidate.toLowerCase();
    if (normalized.length < 2 || seen.has(normalized)) {
      continue;
    }

    seen.add(normalized);
    terms.push(candidate);
  }

  return terms;
}
