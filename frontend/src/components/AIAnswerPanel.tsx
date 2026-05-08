import type { AIAnswerRecord } from "../types";

interface AIAnswerPanelProps {
  answers: AIAnswerRecord[];
  latestStatus: string | null;
}

export function AIAnswerPanel({ answers, latestStatus }: AIAnswerPanelProps) {
  const latestAnswer = answers[0] ?? null;

  return (
    <section className="panel">
      <h2>AI Answer Panel</h2>
      {latestStatus ? <div className="status-chip">{latestStatus}</div> : null}
      {latestAnswer ? (
        <div className="answer-stack">
          <div className="answer-card latest-answer">
            <div className="answer-label">Latest Question</div>
            <strong>{latestAnswer.question_text}</strong>
            <div className="answer-label">Short Answer</div>
            <div>{latestAnswer.text}</div>
          </div>
          {answers.length > 1 ? (
            <div className="answer-history">
              <h3>Recent Answers</h3>
              {answers.slice(1, 4).map((answer) => (
                <div key={answer.id} className="answer-card">
                  <strong>{answer.question_text}</strong>
                  <div>{answer.text}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <div className="muted">Ask a question to trigger an AI answer.</div>
      )}
    </section>
  );
}
