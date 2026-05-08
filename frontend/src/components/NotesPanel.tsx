import type { TranscriptSegment } from "../types";

interface NotesPanelProps {
  segments: TranscriptSegment[];
}

function uniqueByText(segments: TranscriptSegment[]): TranscriptSegment[] {
  const seen = new Set<string>();
  return segments.filter((segment) => {
    const key = `${segment.phrase_type}:${segment.text}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

export function NotesPanel({ segments }: NotesPanelProps) {
  const questions = uniqueByText(
    segments.filter((segment) => segment.phrase_type === "question"),
  );
  const important = uniqueByText(
    segments.filter(
      (segment) =>
        segment.phrase_type === "important" || segment.phrase_type === "exam_hint",
    ),
  );
  const notes = uniqueByText(
    segments.filter((segment) => segment.phrase_type === "normal"),
  );

  return (
    <aside className="notes-panel panel">
      <h2>Notes Panel</h2>
      <div className="notes-group">
        <h3>Notes</h3>
        {notes.length === 0 ? (
          <div className="muted">No notes yet.</div>
        ) : (
          notes.map((segment) => <div key={segment.id}>{segment.text}</div>)
        )}
      </div>
      <div className="notes-group">
        <h3>Questions</h3>
        {questions.length === 0 ? (
          <div className="muted">No questions yet.</div>
        ) : (
          questions.map((segment) => <div key={segment.id}>{segment.text}</div>)
        )}
      </div>
      <div className="notes-group">
        <h3>Important</h3>
        {important.length === 0 ? (
          <div className="muted">No important items yet.</div>
        ) : (
          important.map((segment) => <div key={segment.id}>{segment.text}</div>)
        )}
      </div>
    </aside>
  );
}
