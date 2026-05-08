interface QuickInsertPanelProps {
  onPickExample: (text: string) => void;
}

const EXAMPLES = [
  {
    label: "Question",
    text: "Was ist der Unterschied zwischen RAID 0 und RAID 1?",
  },
  {
    label: "Important",
    text: "Das ist wichtig fur die Prufung, bitte merken.",
  },
  {
    label: "Deadline",
    text: "Bitte bis 12 Uhr die Aufgabe abgeben.",
  },
  {
    label: "Task",
    text: "Macht die Hausaufgabe und sendet die Losung morgen.",
  },
  {
    label: "Definition",
    text: "RAID 1 ist eine Spiegelung von Daten auf zwei Festplatten.",
  },
  {
    label: "Exam Hint",
    text: "Das kommt oft in der IHK Prufung dran.",
  },
];

export function QuickInsertPanel({ onPickExample }: QuickInsertPanelProps) {
  return (
    <section className="panel">
      <h2>0.3 Quick Tests</h2>
      <div className="quick-test-grid">
        {EXAMPLES.map((example) => (
          <button
            key={example.label}
            className="secondary-button"
            type="button"
            onClick={() => onPickExample(example.text)}
          >
            {example.label}
          </button>
        ))}
      </div>
    </section>
  );
}
