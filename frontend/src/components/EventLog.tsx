import type { AIAnswerRecord, TranscriptSegment } from "../types";

interface EventLogProps {
  segments: TranscriptSegment[];
  answers: AIAnswerRecord[];
  rejections: string[];
  statusMessages: string[];
}

export function EventLog({ segments, answers, rejections, statusMessages }: EventLogProps) {
  return (
    <section className="panel event-log">
      <h2>Transcript + Event Log</h2>
      <div className="log-columns">
        <div>
          <h3>Accepted Transcript</h3>
          {segments.length === 0 ? (
            <div className="muted">No accepted transcript yet.</div>
          ) : (
            segments
              .slice()
              .reverse()
              .map((segment) => (
                <div key={segment.id} className="log-item">
                  <strong>[{segment.timestamp}]</strong> {segment.phrase_type} - {segment.text}
                </div>
              ))
          )}
        </div>
        <div>
          <h3>AI Answers</h3>
          {answers.length === 0 ? (
            <div className="muted">No AI answers yet.</div>
          ) : (
            answers.map((answer) => (
              <div key={answer.id} className="log-item answer-log">
                <strong>{answer.question_text}</strong>
                <div>{answer.text}</div>
              </div>
            ))
          )}
          <h3>Rejected</h3>
          {rejections.length === 0 ? (
            <div className="muted">No rejections yet.</div>
          ) : (
            rejections.map((entry, index) => (
              <div key={`${entry}-${index}`} className="log-item rejection">
                {entry}
              </div>
            ))
          )}
          <h3>Status</h3>
          {statusMessages.length === 0 ? (
            <div className="muted">No status messages yet.</div>
          ) : (
            statusMessages.map((entry, index) => (
              <div key={`${entry}-${index}`} className="log-item status">
                {entry}
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
