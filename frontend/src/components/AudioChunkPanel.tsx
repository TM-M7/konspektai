import { useEffect, useRef, useState, type FormEvent } from "react";

import { analyzeAudioBlob, blobToBase64, detectAudioFormat } from "../lib/audio";

interface AudioChunkPanelProps {
  disabled: boolean;
  initialText?: string;
  onSend: (payload: {
    timestamp: string;
    durationSeconds: number;
    averageVolume: number;
    peakVolume: number;
    simulatedText: string;
    languageHint: string;
    source?: "manual_simulated" | "browser_microphone" | "tauri_microphone";
    audioBase64?: string | null;
    audioFormat?: string | null;
  }) => Promise<void>;
}

function buildTimestampFromNow(): string {
  const now = new Date();
  return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
}

export function AudioChunkPanel({ disabled, initialText, onSend }: AudioChunkPanelProps) {
  const [timestamp, setTimestamp] = useState("00:42");
  const [durationSeconds, setDurationSeconds] = useState("4.0");
  const [averageVolume, setAverageVolume] = useState("0.44");
  const [peakVolume, setPeakVolume] = useState("0.62");
  const [languageHint, setLanguageHint] = useState("de");
  const [simulatedText, setSimulatedText] = useState(initialText ?? "Was ist RAID 1?");
  const [recorderState, setRecorderState] = useState<"idle" | "recording" | "processing">("idle");
  const [recorderMessage, setRecorderMessage] = useState("Browser recorder ready.");
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    setSimulatedText(initialText ?? "Was ist RAID 1?");
  }, [initialText]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSend({
      timestamp,
      durationSeconds: Number(durationSeconds),
      averageVolume: Number(averageVolume),
      peakVolume: Number(peakVolume),
      simulatedText,
      languageHint,
      source: "manual_simulated",
    });
  }

  async function handleStartRecording() {
    if (!("MediaRecorder" in window) || !navigator.mediaDevices?.getUserMedia) {
      setRecorderMessage("MediaRecorder API is not available in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      recordedChunksRef.current = [];
      mediaRecorderRef.current = recorder;
      mediaStreamRef.current = stream;

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      });

      recorder.addEventListener("stop", async () => {
        setRecorderState("processing");
        try {
          const blob = new Blob(recordedChunksRef.current, { type: recorder.mimeType || "audio/webm" });
          setRecordedBlob(blob);

          const metrics = await analyzeAudioBlob(blob);
          setDurationSeconds(String(metrics.durationSeconds || 3));
          setAverageVolume(String(metrics.averageVolume));
          setPeakVolume(String(metrics.peakVolume));
          setTimestamp(buildTimestampFromNow());
          setRecorderMessage("Recording processed. Review fallback text or send directly.");
        } catch (error) {
          setRecorderMessage(
            error instanceof Error ? error.message : "Failed to process recorded audio.",
          );
        } finally {
          setRecorderState("idle");
        }
      });

      recorder.start();
      setRecorderState("recording");
      setRecorderMessage("Recording in progress...");
    } catch (error) {
      setRecorderMessage(error instanceof Error ? error.message : "Microphone access failed.");
    }
  }

  function cleanupRecorder() {
    mediaRecorderRef.current = null;
    if (mediaStreamRef.current) {
      for (const track of mediaStreamRef.current.getTracks()) {
        track.stop();
      }
    }
    mediaStreamRef.current = null;
  }

  function handleStopRecording() {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== "recording") {
      return;
    }

    recorder.stop();
    cleanupRecorder();
  }

  async function handleSendRecording() {
    if (!recordedBlob) {
      setRecorderMessage("Record audio first.");
      return;
    }

    setRecorderState("processing");
    try {
      const audioBase64 = await blobToBase64(recordedBlob);
      const audioFormat = detectAudioFormat(recordedBlob.type || "audio/webm");

      await onSend({
        timestamp,
        durationSeconds: Number(durationSeconds),
        averageVolume: Number(averageVolume),
        peakVolume: Number(peakVolume),
        simulatedText,
        languageHint,
        source: "browser_microphone",
        audioBase64,
        audioFormat,
      });

      setRecorderMessage("Recorded chunk sent to backend.");
    } catch (error) {
      setRecorderMessage(error instanceof Error ? error.message : "Failed to send recording.");
    } finally {
      setRecorderState("idle");
    }
  }

  return (
    <section className="panel">
      <h2>0.8 Audio Capture + Simulator</h2>
      <div className="recorder-toolbar">
        <button disabled={disabled || recorderState === "recording"} onClick={handleStartRecording} type="button">
          Start Recording
        </button>
        <button
          className="secondary-button"
          disabled={disabled || recorderState !== "recording"}
          onClick={handleStopRecording}
          type="button"
        >
          Stop Recording
        </button>
        <button
          className="secondary-button"
          disabled={disabled || !recordedBlob || recorderState === "processing"}
          onClick={() => void handleSendRecording()}
          type="button"
        >
          Send Recorded Chunk
        </button>
      </div>
      <div className="status-chip">{recorderMessage}</div>

      <form className="ingest-form" onSubmit={handleSubmit}>
        <div className="audio-grid">
          <label>
            Timestamp
            <input value={timestamp} onChange={(event) => setTimestamp(event.target.value)} />
          </label>
          <label>
            Duration
            <input
              value={durationSeconds}
              onChange={(event) => setDurationSeconds(event.target.value)}
              type="number"
              min="0"
              step="0.1"
            />
          </label>
          <label>
            Avg volume
            <input
              value={averageVolume}
              onChange={(event) => setAverageVolume(event.target.value)}
              type="number"
              min="0"
              max="1"
              step="0.01"
            />
          </label>
          <label>
            Peak volume
            <input
              value={peakVolume}
              onChange={(event) => setPeakVolume(event.target.value)}
              type="number"
              min="0"
              max="1"
              step="0.01"
            />
          </label>
          <label>
            Language hint
            <input value={languageHint} onChange={(event) => setLanguageHint(event.target.value)} />
          </label>
        </div>
        <label>
          Fallback transcript for manual mode
          <textarea
            rows={4}
            value={simulatedText}
            onChange={(event) => setSimulatedText(event.target.value)}
          />
        </label>
        <button disabled={disabled} type="submit">
          {disabled ? "Start a session first" : "Send simulated audio chunk"}
        </button>
      </form>
    </section>
  );
}
