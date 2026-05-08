from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from app.config import AppConfig
from app.db import Database
from app.schemas import AudioChunkIngestRequest, AudioChunkIngestResponse, AudioChunkRecord, TranscriptIngestRequest
from app.services.pipeline import TranscriptPipeline


class AudioChunkService:
    def __init__(self, database: Database, pipeline: TranscriptPipeline, config: AppConfig) -> None:
        self.database = database
        self.pipeline = pipeline
        self.config = config

    def ingest_chunk(self, payload: AudioChunkIngestRequest) -> AudioChunkIngestResponse:
        transcript_text = payload.simulated_text
        detected_language = self._detect_language(transcript_text, payload.language_hint)

        if self.config.transcription_mode == "whisper":
            transcript_text, detected_language = self._transcribe_audio(payload)

        validation_reason = self._validate_chunk(payload, transcript_text)
        if validation_reason is not None:
            chunk = self._store_chunk(payload, transcript_text, detected_language, validation_reason, None)
            return AudioChunkIngestResponse(accepted=False, reason=validation_reason, audio_chunk=chunk)

        transcript_response = self.pipeline.ingest(
            TranscriptIngestRequest(
                session_id=payload.session_id,
                timestamp=payload.timestamp,
                language=detected_language or payload.language_hint or "und",
                text=transcript_text,
                confidence=self._derive_confidence(payload),
                volume=payload.average_volume,
            )
        )

        if not transcript_response.accepted:
            chunk = self._store_chunk(
                payload,
                transcript_text,
                detected_language,
                transcript_response.reason or "empty_transcript",
                None,
            )
            return AudioChunkIngestResponse(
                accepted=False,
                reason=transcript_response.reason,
                audio_chunk=chunk,
            )

        segment = transcript_response.segment
        chunk = self._store_chunk(payload, transcript_text, detected_language, "accepted", segment.id if segment else None)
        return AudioChunkIngestResponse(accepted=True, audio_chunk=chunk, segment=segment)

    def list_chunks(self, session_id: int) -> list[AudioChunkRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, ts, duration_seconds, average_volume, peak_volume, source,
                       language_hint, simulated_text, detected_language, validation_status,
                       transcript_segment_id
                FROM audio_chunks
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return [
            AudioChunkRecord(
                id=row["id"],
                session_id=row["session_id"],
                timestamp=row["ts"],
                duration_seconds=row["duration_seconds"],
                average_volume=row["average_volume"],
                peak_volume=row["peak_volume"],
                source=row["source"],
                language_hint=row["language_hint"],
                simulated_text=row["simulated_text"],
                detected_language=row["detected_language"],
                validation_status=row["validation_status"],
                transcript_segment_id=row["transcript_segment_id"],
            )
            for row in rows
        ]

    def _validate_chunk(self, payload: AudioChunkIngestRequest, transcript_text: str) -> str | None:
        if payload.duration_seconds < self.config.audio_chunk_min_duration_seconds:
            return "invalid_duration"
        if payload.duration_seconds > self.config.audio_chunk_max_duration_seconds:
            return "invalid_duration"
        if not transcript_text.strip():
            return "empty_transcript"
        if payload.average_volume < self.config.low_volume_threshold:
            return "silence"
        if payload.peak_volume > self.config.high_volume_threshold:
            return "too_loud"
        return None

    def _derive_confidence(self, payload: AudioChunkIngestRequest) -> float:
        duration_factor = min(payload.duration_seconds / 5.0, 1.0)
        volume_factor = min(max(payload.average_volume, 0.1), 1.0)
        return round(max(0.5, min(0.98, 0.55 + duration_factor * 0.2 + volume_factor * 0.2)), 2)

    def _detect_language(self, text: str, hint: str | None) -> str | None:
        if hint:
            return hint
        normalized = text.lower()
        german_markers = ("was", "wie", "warum", "prufung", "der", "die", "und")
        russian_markers = ("chto", "kak", "eto", "i", "dlya")
        if any(marker in normalized for marker in german_markers):
            return "de"
        if any(marker in normalized for marker in russian_markers):
            return "ru"
        if normalized.strip():
            return "en"
        return None

    def _transcribe_audio(self, payload: AudioChunkIngestRequest) -> tuple[str, str | None]:
        if not payload.audio_base64:
            raise ValueError("audio_base64_required")

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ValueError("faster_whisper_not_installed") from exc

        audio_bytes = base64.b64decode(payload.audio_base64)
        suffix = f".{(payload.audio_format or 'wav').lower()}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        try:
            model = WhisperModel(self.config.whisper_model_size, compute_type=self.config.whisper_compute_type)
            segments, info = model.transcribe(str(temp_path))
            text = " ".join(segment.text.strip() for segment in segments).strip()
            language = getattr(info, "language", None)
        finally:
            temp_path.unlink(missing_ok=True)

        if not text:
            raise ValueError("empty_transcript")
        return text, language

    def _store_chunk(
        self,
        payload: AudioChunkIngestRequest,
        transcript_text: str,
        detected_language: str | None,
        validation_status: str,
        transcript_segment_id: int | None,
    ) -> AudioChunkRecord:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO audio_chunks(
                    session_id, ts, duration_seconds, average_volume, peak_volume, source,
                    language_hint, simulated_text, detected_language, validation_status,
                    transcript_segment_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.session_id,
                    payload.timestamp,
                    payload.duration_seconds,
                    payload.average_volume,
                    payload.peak_volume,
                    payload.source,
                    payload.language_hint,
                    transcript_text,
                    detected_language,
                    validation_status,
                    transcript_segment_id,
                ),
            )
            connection.commit()
            chunk_id = int(cursor.lastrowid)

        return AudioChunkRecord(
            id=chunk_id,
            session_id=payload.session_id,
            timestamp=payload.timestamp,
            duration_seconds=payload.duration_seconds,
            average_volume=payload.average_volume,
            peak_volume=payload.peak_volume,
            source=payload.source,
            language_hint=payload.language_hint,
            simulated_text=transcript_text,
            detected_language=detected_language,
            validation_status=validation_status,
            transcript_segment_id=transcript_segment_id,
        )
