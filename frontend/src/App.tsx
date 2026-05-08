import { useEffect, useState } from "react";

import {
  createSession,
  exportAnkiCsv,
  exportMarkdown,
  generateAnswer,
  generateFlashcards,
  getBackendBaseUrl,
  getSession,
  ingestAudioChunk,
  ingestTranscript,
  listAnswers,
  listAudioChunks,
  listExports,
  listFlashcards,
  listSegments,
  listSessions,
  renameSession,
} from "./api/backend";
import { AIAnswerPanel } from "./components/AIAnswerPanel";
import { AudioChunkPanel } from "./components/AudioChunkPanel";
import { DesktopStatusPanel } from "./components/DesktopStatusPanel";
import { EventLog } from "./components/EventLog";
import { MaterialsPanel } from "./components/MaterialsPanel";
import { NotesPanel } from "./components/NotesPanel";
import { QuickInsertPanel } from "./components/QuickInsertPanel";
import { SessionControls } from "./components/SessionControls";
import { SubtitleOverlay } from "./components/SubtitleOverlay";
import { TextIngestBox } from "./components/TextIngestBox";
import { getRuntimeLabel } from "./lib/desktop";
import { readActiveSessionId, writeActiveSessionId } from "./lib/sessionStorage";
import type {
  AIAnswerRecord,
  AudioChunkRecord,
  ExportRecord,
  FlashcardRecord,
  SessionResponse,
  SessionSummary,
  TranscriptSegment,
} from "./types";

export default function App() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [answers, setAnswers] = useState<AIAnswerRecord[]>([]);
  const [audioChunks, setAudioChunks] = useState<AudioChunkRecord[]>([]);
  const [flashcards, setFlashcards] = useState<FlashcardRecord[]>([]);
  const [exports, setExports] = useState<ExportRecord[]>([]);
  const [rejections, setRejections] = useState<string[]>([]);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [answerStatus, setAnswerStatus] = useState<string | null>(null);
  const [sessionBusy, setSessionBusy] = useState(false);
  const [requestBusy, setRequestBusy] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [uiError, setUiError] = useState<string | null>(null);
  const [draftText, setDraftText] = useState("Heute sprechen wir uber RAID.");

  async function refreshSessions(activeSessionId?: number | null) {
    const nextSessions = await listSessions();
    setSessions(nextSessions);

    if (activeSessionId !== undefined) {
      writeActiveSessionId(activeSessionId);
    }
  }

  async function loadSessionWorkspace(sessionId: number) {
    const [sessionSummary, nextSegments, nextAnswers, nextAudioChunks, nextFlashcards, nextExports] =
      await Promise.all([
        getSession(sessionId),
        listSegments(sessionId),
        listAnswers(sessionId),
        listAudioChunks(sessionId),
        listFlashcards(sessionId),
        listExports(sessionId),
      ]);

    setSession({ id: sessionSummary.id, title: sessionSummary.title });
    setSegments(nextSegments);
    setAnswers(nextAnswers);
    setAudioChunks(nextAudioChunks);
    setFlashcards(nextFlashcards);
    setExports(nextExports);
    setRejections([]);
    setAnswerStatus(null);
    writeActiveSessionId(sessionId);
  }

  useEffect(() => {
    let isMounted = true;

    async function bootstrap() {
      setLoadingSessions(true);
      try {
        const nextSessions = await listSessions();
        if (!isMounted) {
          return;
        }

        setSessions(nextSessions);
        const restoredSessionId = readActiveSessionId();
        if (restoredSessionId) {
          try {
            await loadSessionWorkspace(restoredSessionId);
            if (isMounted) {
              setStatusMessages((current) => [
                `Session restored from local state (#${restoredSessionId})`,
                ...current,
              ]);
            }
          } catch {
            if (isMounted) {
              writeActiveSessionId(null);
            }
          }
        }
      } catch (error) {
        if (isMounted) {
          setUiError(error instanceof Error ? error.message : "Failed to load sessions");
        }
      } finally {
        if (isMounted) {
          setLoadingSessions(false);
        }
      }
    }

    void bootstrap();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleCreateSession(title: string) {
    setUiError(null);
    setSessionBusy(true);
    try {
      const created = await createSession(title);
      setSession(created);
      setSegments([]);
      setAnswers([]);
      setAudioChunks([]);
      setFlashcards([]);
      setExports([]);
      setRejections([]);
      setAnswerStatus(null);
      setStatusMessages((current) => [
        `Session created: ${created.title} (#${created.id})`,
        ...current,
      ]);
      await refreshSessions(created.id);
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Session creation failed");
    } finally {
      setSessionBusy(false);
    }
  }

  async function handleRenameSession(title: string) {
    if (!session) {
      setUiError("Create or resume a session before renaming it.");
      return;
    }

    setUiError(null);
    setSessionBusy(true);
    try {
      const updated = await renameSession(session.id, title);
      setSession(updated);
      await refreshSessions(updated.id);
      setStatusMessages((current) => [`Session renamed: ${updated.title}`, ...current]);
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Session rename failed");
    } finally {
      setSessionBusy(false);
    }
  }

  async function handleResumeSession(sessionId: number) {
    setUiError(null);
    setSessionBusy(true);
    try {
      await loadSessionWorkspace(sessionId);
      await refreshSessions(sessionId);
      setStatusMessages((current) => [`Session resumed: #${sessionId}`, ...current]);
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Session load failed");
    } finally {
      setSessionBusy(false);
    }
  }

  async function handleSend(payload: {
    timestamp: string;
    language: string;
    text: string;
    confidence: number;
  }) {
    if (!session) {
      setUiError("Create a session before sending transcript text.");
      return;
    }

    setUiError(null);
    setRequestBusy(true);
    try {
      const response = await ingestTranscript({
        sessionId: session.id,
        timestamp: payload.timestamp,
        language: payload.language,
        text: payload.text,
        confidence: payload.confidence,
      });

      if (!response.accepted || !response.segment) {
        setRejections((current) => [
          `Rejected: ${response.reason ?? "unknown"} - ${payload.text}`,
          ...current,
        ]);
        setStatusMessages((current) => [
          `Ingest rejected: ${response.reason ?? "unknown"}`,
          ...current,
        ]);
        return;
      }

      const acceptedSegment = response.segment;
      setSegments((current) => [...current, acceptedSegment]);
      setStatusMessages((current) => [
        `Segment accepted: ${acceptedSegment.phrase_type}`,
        ...current,
      ]);
      await refreshSessions(session.id);

      if (acceptedSegment.show_answer && acceptedSegment.question_id) {
        setAnswerStatus("AI thinking...");
        const answer = await generateAnswer(acceptedSegment.question_id);
        setAnswers((current) => [answer, ...current.filter((item) => item.id !== answer.id)]);
        setAnswerStatus("AI answer ready");
        setStatusMessages((current) => [
          `Answer generated for question #${acceptedSegment.question_id}`,
          ...current,
        ]);
        await refreshSessions(session.id);
      }
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Ingest failed");
    } finally {
      setRequestBusy(false);
    }
  }

  async function handleGenerateFlashcards() {
    if (!session) {
      setUiError("Create a session before generating flashcards.");
      return;
    }

    setUiError(null);
    try {
      const generated = await generateFlashcards(session.id);
      setFlashcards(generated);
      setStatusMessages((current) => [
        `Generated ${generated.length} flashcards`,
        ...current,
      ]);
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Flashcard generation failed");
    }
  }

  async function handleAudioChunkSend(payload: {
    timestamp: string;
    durationSeconds: number;
    averageVolume: number;
    peakVolume: number;
    simulatedText: string;
    languageHint: string;
    source?: "manual_simulated" | "browser_microphone" | "tauri_microphone";
    audioBase64?: string | null;
    audioFormat?: string | null;
  }) {
    if (!session) {
      setUiError("Create a session before sending audio.");
      return;
    }

    setUiError(null);
    setRequestBusy(true);
    try {
      const response = await ingestAudioChunk({
        sessionId: session.id,
        timestamp: payload.timestamp,
        durationSeconds: payload.durationSeconds,
        averageVolume: payload.averageVolume,
        peakVolume: payload.peakVolume,
        simulatedText: payload.simulatedText,
        languageHint: payload.languageHint,
        source: payload.source,
        audioBase64: payload.audioBase64,
        audioFormat: payload.audioFormat,
      });

      if (response.audio_chunk) {
        const acceptedChunk = response.audio_chunk;
        setAudioChunks((current) => [...current, acceptedChunk]);
        setStatusMessages((current) => [
          `Audio chunk: ${acceptedChunk.validation_status} (${acceptedChunk.source})`,
          ...current,
        ]);
      }

      if (!response.accepted || !response.segment) {
        setRejections((current) => [
          `Audio rejected: ${response.reason ?? "unknown"} - ${payload.simulatedText}`,
          ...current,
        ]);
        return;
      }

      const acceptedSegment = response.segment;
      setSegments((current) => [...current, acceptedSegment]);
      await refreshSessions(session.id);
      if (acceptedSegment.show_answer && acceptedSegment.question_id) {
        setAnswerStatus("AI thinking...");
        const answer = await generateAnswer(acceptedSegment.question_id);
        setAnswers((current) => [answer, ...current.filter((item) => item.id !== answer.id)]);
        setAnswerStatus("AI answer ready");
        await refreshSessions(session.id);
      }
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Audio chunk ingest failed");
    } finally {
      setRequestBusy(false);
    }
  }

  async function handleExportMarkdown() {
    if (!session) {
      setUiError("Create a session before exporting.");
      return;
    }

    setUiError(null);
    try {
      const exported = await exportMarkdown(session.id);
      setExports((current) => [exported, ...current]);
      setStatusMessages((current) => [`Markdown exported: ${exported.path}`, ...current]);
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Markdown export failed");
    }
  }

  async function handleExportAnkiCsv() {
    if (!session) {
      setUiError("Create a session before exporting.");
      return;
    }

    setUiError(null);
    try {
      const exported = await exportAnkiCsv(session.id);
      setExports((current) => [exported, ...current]);
      setStatusMessages((current) => [`Anki CSV exported: ${exported.path}`, ...current]);
    } catch (error) {
      setUiError(error instanceof Error ? error.message : "Anki CSV export failed");
    }
  }

  return (
    <main className="app-shell">
      <SubtitleOverlay segments={segments} />

      <div className="workspace">
        <NotesPanel segments={segments} />

        <section className="main-column">
          <header className="hero panel">
            <h1>konspektai 0.8 desktop-ready study shell</h1>
            <p>
              Browser-first study workflow with session restore, microphone capture, local stubs,
              and a prepared Tauri desktop layer.
            </p>
            <div className="endpoint-list">
              <span>API: {getBackendBaseUrl()}</span>
              <span>Runtime: {getRuntimeLabel()}</span>
              <span>Flow: HTTP-first with optional browser audio capture</span>
            </div>
            {uiError ? <div className="error-banner">{uiError}</div> : null}
          </header>

          <SessionControls
            currentSession={session}
            sessions={sessions}
            isBusy={sessionBusy}
            isLoadingSessions={loadingSessions}
            onCreateSession={handleCreateSession}
            onRenameSession={handleRenameSession}
            onResumeSession={handleResumeSession}
          />

          <DesktopStatusPanel currentSessionTitle={session?.title ?? null} />

          <QuickInsertPanel onPickExample={setDraftText} />

          <TextIngestBox
            disabled={!session || requestBusy}
            initialText={draftText}
            onSend={handleSend}
          />

          <AudioChunkPanel
            disabled={!session || requestBusy}
            initialText={draftText}
            onSend={handleAudioChunkSend}
          />

          <AIAnswerPanel answers={answers} latestStatus={answerStatus} />

          <MaterialsPanel
            flashcards={flashcards}
            exports={exports}
            disabled={!session}
            onGenerateFlashcards={handleGenerateFlashcards}
            onExportMarkdown={handleExportMarkdown}
            onExportAnkiCsv={handleExportAnkiCsv}
          />

          <EventLog
            segments={segments}
            answers={answers}
            rejections={rejections}
            statusMessages={[
              ...statusMessages,
              ...audioChunks
                .slice(-3)
                .map(
                  (chunk) =>
                    `Audio ${chunk.timestamp}: ${chunk.validation_status} (${chunk.detected_language ?? "und"})`,
                ),
            ]}
          />
        </section>
      </div>
    </main>
  );
}
