# konspektai

`konspektai` is a local-first Study Copilot MVP:

- `Tauri + React + TypeScript` for desktop UI
- `Python + FastAPI + WebSocket` for backend orchestration
- `faster-whisper` for speech-to-text
- `Ollama + Qwen` for local AI answers
- `SQLite` for durable session storage

The repository now includes a working backend skeleton built around one rule:

`action -> validation -> log -> error handling -> persistence`

## Current scope

This repo currently implements MVP `0.2` in text-only mode:

- startup dependency checks
- session creation
- transcript segment ingestion
- phrase classification
- SQLite persistence
- WebSocket event broadcasting for UI
- React frontend for manual ingest testing
- tests for API and core logic

This version intentionally avoids microphone capture so we can prove the realtime pipeline first.

## Project layout

```text
backend/
  app/
    main.py
    config.py
    db.py
    logging_setup.py
    schemas.py
    services/
      broadcaster.py
      classifier.py
      health.py
      pipeline.py
  tests/
    test_api.py
    test_classifier.py
    test_pipeline.py
  pyproject.toml
frontend/
  src/
    App.tsx
    api/
      backend.ts
      websocket.ts
    components/
      EventLog.tsx
      NotesPanel.tsx
      SessionControls.tsx
      SubtitleOverlay.tsx
      TextIngestBox.tsx
  package.json
```

## Backend flow

```text
App start
  -> run dependency checks
  -> initialize SQLite
  -> open WebSocket channel

Manual text input
  -> create session
  -> validate payload
  -> reject empty or duplicate text
  -> classify phrase
  -> save to SQLite
  -> broadcast event to UI
  -> render subtitle and notes panels
```

## API overview

`GET /health/startup`

- checks microphone support package
- checks Ollama availability
- checks Ollama model availability
- checks `faster-whisper`
- checks workspace and export directories
- checks SQLite connectivity

`POST /sessions`

- creates a study session from `{ "title": "Test lesson" }`

`POST /ingest`

- accepts transcript chunks
- classifies them
- saves them
- emits a WebSocket event

`GET /sessions/{session_id}/segments`

- reads saved transcript history

`WS /ws/events`

- streams `transcript_segment`, `ingest_rejected`, and `status` events to UI

## Running locally

Start backend:

From [backend/pyproject.toml](/C:/Users/M_M/Documents/GitHub/konspektai/backend/pyproject.toml):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

Start frontend:

From [frontend/package.json](/C:/Users/M_M/Documents/GitHub/konspektai/frontend/package.json):

```bash
cd frontend
npm install
npm run dev
```

## Text-only 0.2 flow

```text
1. Open frontend
2. Click Start Session
3. Type or paste transcript text
4. Send to /ingest
5. Receive WebSocket event
6. Show subtitle overlay
7. Add question/important items to notes panel
```

## Example session request

```json
{
  "title": "Test lesson"
}
```

## Example ingest request

```json
{
  "session_id": 1,
  "timestamp": "00:35",
  "language": "de",
  "text": "Was ist der Unterschied zwischen RAID 0 und RAID 1?",
  "confidence": 0.91
}
```

Response:

```json
{
  "accepted": true,
  "reason": null,
  "segment": {
    "id": 1,
    "session_id": 1,
    "timestamp": "00:35",
    "language": "de",
    "text": "Was ist der Unterschied zwischen RAID 0 und RAID 1?",
    "confidence": 0.91,
    "phrase_type": "question",
    "priority": "high",
    "show_answer": true
  }
}
```

## Verified behavior

- `POST /sessions` uses session-only payload
- empty text returns `accepted: false` with `reason: "empty_text"`
- duplicate text returns `accepted: false` with `reason: "duplicate"`
- question text is classified as `question`
- WebSocket events include `event_type`

## Next recommended milestones

`0.3`

- aggregate terms and deadlines in a richer notes panel
- add better rule-based classification coverage

`0.4`

- Ollama short answers with timeout and fallback status

`0.5`

- flashcards
- PDF/DOCX export

`0.6`

- microphone capture
- faster-whisper integration
- system audio research only after mic path is stable
