import type { TranscriptSegment } from "../types";

interface SubtitleOverlayProps {
  segments: TranscriptSegment[];
}

export function SubtitleOverlay({ segments }: SubtitleOverlayProps) {
  const visibleSegments = segments.slice(-3).reverse();

  return (
    <section className="subtitle-overlay">
      <h2>Live Subtitles</h2>
      <div className="subtitle-list">
        {visibleSegments.length === 0 ? (
          <div className="subtitle-item muted">Waiting for transcript events...</div>
        ) : (
          visibleSegments.map((segment) => (
            <div
              key={segment.id}
              className={`subtitle-item subtitle-${segment.phrase_type}`}
            >
              <span className="subtitle-timestamp">[{segment.timestamp}]</span>
              <span>{segment.text}</span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
