import { buildNotesBuckets } from "../lib/notes";
import type { TranscriptSegment } from "../types";

interface NotesPanelProps {
  segments: TranscriptSegment[];
}

interface NotesSectionProps {
  title: string;
  items: string[];
  emptyText: string;
}

function NotesSection({ title, items, emptyText }: NotesSectionProps) {
  return (
    <div className="notes-group">
      <h3>{title}</h3>
      {items.length === 0 ? (
        <div className="muted">{emptyText}</div>
      ) : (
        items.map((item, index) => <div key={`${title}-${index}`}>{item}</div>)
      )}
    </div>
  );
}

export function NotesPanel({ segments }: NotesPanelProps) {
  const buckets = buildNotesBuckets(segments);
  const summaryCards = [
    { label: "Questions", value: buckets.questions.length },
    { label: "Important", value: buckets.important.length + buckets.examHints.length },
    { label: "Deadlines", value: buckets.deadlines.length },
    { label: "Tasks", value: buckets.tasks.length },
  ];

  return (
    <aside className="notes-panel panel">
      <h2>Notes Panel</h2>
      <div className="notes-summary">
        {summaryCards.map((card) => (
          <div key={card.label} className="summary-card">
            <span className="summary-value">{card.value}</span>
            <span className="summary-label">{card.label}</span>
          </div>
        ))}
      </div>
      <NotesSection
        title="Notes"
        items={buckets.notes.map((segment) => segment.text)}
        emptyText="No notes yet."
      />
      <NotesSection
        title="Questions"
        items={buckets.questions.map((segment) => segment.text)}
        emptyText="No questions yet."
      />
      <NotesSection
        title="Important"
        items={buckets.important.map((segment) => segment.text)}
        emptyText="No important items yet."
      />
      <NotesSection
        title="Exam Hints"
        items={buckets.examHints.map((segment) => segment.text)}
        emptyText="No exam hints yet."
      />
      <NotesSection
        title="Deadlines"
        items={buckets.deadlines.map((segment) => segment.text)}
        emptyText="No deadlines yet."
      />
      <NotesSection
        title="Tasks"
        items={buckets.tasks.map((segment) => segment.text)}
        emptyText="No tasks yet."
      />
      <NotesSection
        title="Definitions"
        items={buckets.definitions.map((segment) => segment.text)}
        emptyText="No definitions yet."
      />
      <NotesSection
        title="Terms"
        items={buckets.terms}
        emptyText="No extracted terms yet."
      />
      <NotesSection
        title="Examples"
        items={buckets.examples.map((segment) => segment.text)}
        emptyText="No examples yet."
      />
    </aside>
  );
}
