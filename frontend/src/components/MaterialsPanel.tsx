import type { ExportRecord, FlashcardRecord } from "../types";

interface MaterialsPanelProps {
  flashcards: FlashcardRecord[];
  exports: ExportRecord[];
  disabled: boolean;
  onGenerateFlashcards: () => Promise<void>;
  onExportMarkdown: () => Promise<void>;
  onExportAnkiCsv: () => Promise<void>;
}

export function MaterialsPanel({
  flashcards,
  exports,
  disabled,
  onGenerateFlashcards,
  onExportMarkdown,
  onExportAnkiCsv,
}: MaterialsPanelProps) {
  return (
    <section className="panel">
      <h2>0.5 Materials</h2>
      <div className="materials-actions">
        <button disabled={disabled} type="button" onClick={() => void onGenerateFlashcards()}>
          Generate Flashcards
        </button>
        <button
          className="secondary-button"
          disabled={disabled}
          type="button"
          onClick={() => void onExportMarkdown()}
        >
          Export Markdown
        </button>
        <button
          className="secondary-button"
          disabled={disabled}
          type="button"
          onClick={() => void onExportAnkiCsv()}
        >
          Export Anki CSV
        </button>
      </div>

      <div className="materials-grid">
        <div>
          <h3>Flashcards</h3>
          {flashcards.length === 0 ? (
            <div className="muted">No flashcards yet.</div>
          ) : (
            flashcards.map((card) => (
              <div key={card.id} className="answer-card">
                <strong>{card.front_text}</strong>
                <div>{card.back_text}</div>
              </div>
            ))
          )}
        </div>

        <div>
          <h3>Exports</h3>
          {exports.length === 0 ? (
            <div className="muted">No exports yet.</div>
          ) : (
            exports.map((item) => (
              <div key={item.id} className="log-item status">
                <strong>{item.export_type}</strong>
                <div>{item.path}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
