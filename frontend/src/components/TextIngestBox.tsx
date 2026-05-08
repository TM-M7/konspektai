import { useEffect, useState, type FormEvent } from "react";

interface TextIngestBoxProps {
  disabled: boolean;
  initialText?: string;
  onSend: (payload: {
    timestamp: string;
    language: string;
    text: string;
    confidence: number;
  }) => Promise<void>;
}

export function TextIngestBox({ disabled, initialText, onSend }: TextIngestBoxProps) {
  const [timestamp, setTimestamp] = useState("00:01");
  const [language, setLanguage] = useState("de");
  const [confidence, setConfidence] = useState("0.95");
  const [text, setText] = useState(initialText ?? "Heute sprechen wir uber RAID.");

  useEffect(() => {
    if (initialText !== undefined) {
      setText(initialText);
    }
  }, [initialText]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSend({
      timestamp,
      language,
      text,
      confidence: Number(confidence),
    });
  }

  return (
    <section className="panel">
      <h2>Manual Ingest</h2>
      <form className="ingest-form" onSubmit={handleSubmit}>
        <div className="ingest-grid">
          <label>
            Timestamp
            <input
              value={timestamp}
              onChange={(event) => setTimestamp(event.target.value)}
              placeholder="00:35"
            />
          </label>
          <label>
            Language
            <input
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              placeholder="de"
            />
          </label>
          <label>
            Confidence
            <input
              value={confidence}
              onChange={(event) => setConfidence(event.target.value)}
              placeholder="0.91"
              type="number"
              min="0"
              max="1"
              step="0.01"
            />
          </label>
        </div>
        <label>
          Transcript text
          <textarea
            rows={5}
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Was ist der Unterschied zwischen RAID 0 und RAID 1?"
          />
        </label>
        <button disabled={disabled} type="submit">
          {disabled ? "Start a session first" : "Send to ingest"}
        </button>
      </form>
    </section>
  );
}
