# konspektai

`konspektai` is a local-first Study Copilot MVP that is now in `0.8` desktop-ready mode.

- `React + TypeScript + Vite` for the current UI
- `Python + FastAPI` for local orchestration
- `SQLite` for durable storage
- optional runtime `Ollama` and `faster-whisper`
- browser microphone capture for manual desktop-style testing
- prepared `Tauri` shell scaffold for packaging and tray support

Core rule:

`action -> validation -> log -> error handling -> persistence`

## Current Scope

This repo currently implements:

- fast local startup checks
- session creation, listing, restore, and rename flow
- transcript ingestion
- phrase classification
- SQLite persistence
- deterministic local stub answers over HTTP
- optional Ollama runtime mode outside tests
- simulated audio chunk ingestion
- browser microphone recording and audio upload
- optional faster-whisper runtime mode outside tests
- structured notes buckets
- flashcard generation
- Markdown export
- Anki CSV export
- frontend session restore from local state
- Tauri desktop scaffold with tray-focused shell setup
- backend and API tests
- 60 second test timeout guard

Current strategy:

- no real Ollama in tests
- no real Whisper in tests
- no waiting on WebSocket for correctness
- no long health checks
- HTTP-first interaction flow
- browser recording is allowed for runtime, but tests stay synthetic and fast

## Project Layout

```text
backend/
  app/
  tests/
frontend/
  src/
src-tauri/
  src/
data/
Versions.md
README.md
```

## Runtime Flow

```text
App start
  -> fast local health checks
  -> initialize SQLite
  -> load saved sessions
  -> restore last active session if available

Manual text flow
  -> create or resume session
  -> validate payload
  -> reject empty or duplicate text
  -> classify phrase
  -> persist segment
  -> generate answer for questions on demand

Browser audio flow
  -> capture microphone chunk in browser
  -> estimate duration and volume locally
  -> send audio chunk to backend
  -> manual mode: use fallback transcript
  -> whisper mode: transcribe audio payload
  -> persist accepted chunk and transcript

Materials flow
  -> generate flashcards
  -> export Markdown
  -> export Anki CSV
```

## API Overview

`GET /health/startup`

- fast local checks only
- reports current runtime modes

`POST /sessions`

- creates a study session from `{ "title": "Test lesson" }`

`GET /sessions`

- returns recent sessions with counts for transcript, questions, and answers

`GET /sessions/{session_id}`

- returns one session summary

`PATCH /sessions/{session_id}`

- renames a session

`POST /ingest`

- accepts transcript text
- validates it
- stores it
- returns accepted or rejected result immediately

`POST /audio/chunks`

- accepts simulated or browser-recorded audio chunk payloads
- validates duration and volume
- uses fallback transcript in manual mode
- can use `faster-whisper` in whisper mode

`POST /questions/{question_id}/answer`

- generates and saves a deterministic local stub answer
- can use Ollama when `KONSPEKTAI_ANSWER_MODE=ollama`

## Running Locally

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

Optional runtime extras:

```powershell
pip install -e .[runtime]
$env:KONSPEKTAI_ANSWER_MODE="ollama"
$env:KONSPEKTAI_TRANSCRIPTION_MODE="whisper"
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Desktop shell preparation:

```powershell
cd frontend
npm run desktop:dev
npm run desktop:build
```

Note:

- `desktop:dev` and `desktop:build` need Rust `cargo` and a Tauri CLI/runtime setup
- those tools are not installed on this machine right now, so the desktop scaffold is prepared but not locally build-verified yet

## Verified Behavior

- `POST /sessions` uses session-only payload
- session list and rename endpoints work
- empty text returns `accepted: false` with `reason: "empty_text"`
- duplicate text returns `accepted: false` with `reason: "duplicate"`
- question text is classified as `question`
- browser microphone chunks are accepted by the same audio pipeline
- answers are generated locally without Ollama in tests
- real Ollama can be enabled for runtime without entering tests
- real faster-whisper can be enabled for runtime without entering tests
- exports are written to the local export directory
- test suite has a 60 second timeout guard

## Versions

Version history, roadmap, and future desktop notes now live in [Versions.md](/C:/Users/M_M/Documents/GitHub/konspektai/Versions.md).
