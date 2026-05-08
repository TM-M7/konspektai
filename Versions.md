# Versions

## Current Stage

Project status: `0.8` desktop-ready integration phase.

What is already true:

- frontend and backend work in HTTP-first mode
- browser microphone recording is available for runtime testing
- session restore and recent session management are in place
- real `Ollama` and `faster-whisper` can be enabled at runtime
- tests still avoid real models and stay fast
- `src-tauri/` is prepared for tray-oriented desktop packaging

What is not yet fully verified on this machine:

- local Tauri build execution
- packaged desktop installer output

Reason:

- `cargo` is not installed
- `tauri` CLI is not installed

## `0.1` Backend Foundation

New functions:

- FastAPI backend skeleton
- SQLite transcript persistence
- ingest pipeline
- validation and duplicate rejection
- startup health checks
- backend tests

Focus:
build a backend that does not fall apart under basic workflow pressure.

## `0.2` Text-First Flow

New functions:

- manual text ingest frontend
- subtitle overlay prototype
- notes panel prototype
- accepted and rejected transcript flow

Focus:
prove frontend and backend interaction before audio capture.

## `0.3` Smarter Study Structure

New functions:

- richer phrase classification
- structured notes buckets
- question extraction
- definition and exam hint detection
- cleaner session organization

Focus:
make study data useful before layering more features on top.

## `0.4` Local Answer Flow

New functions:

- deterministic local short answers for detected questions
- answer persistence
- HTTP-first answer requests
- no real Ollama dependency during tests

Focus:
fast and predictable answer generation during development.

## `0.5` Study Materials & Export

New functions:

- flashcard generation
- Markdown session export
- Anki CSV export
- materials service
- frontend controls for flashcards and exports
- export persistence

Focus:
turn sessions into reusable study material.

## `0.6` Stability & Reliability

New functions:

- stronger validation
- better error handling
- duplicate prevention improvements
- SQLite stability improvements
- performance limits and timeouts
- safer export handling
- test coverage expansion
- test timeout guardrails

Focus:
make the system reliable before adding more complex functionality.

## `0.7` Audio-Ready Runtime

New functions:

- simulated audio chunk ingestion
- chunk duration validation
- silence and loudness validation
- stub language detection for chunks
- audio chunk persistence
- optional real Whisper runtime mode
- optional real Ollama runtime mode
- browser microphone recording path prepared through backend audio endpoint

Focus:
prepare the architecture for real classroom input without making tests slow.

## `0.8` Desktop Integration

New functions:

- `src-tauri/` desktop shell scaffold added
- tray-focused desktop runtime skeleton
- local application build commands added to frontend scripts
- desktop runtime detection in the frontend
- browser microphone recording added to the site
- session listing, restore, and rename flow
- active session restore from local browser storage
- README updated to reflect real project state

Focus:
make KonspektAI behave like a real local application instead of only a dev page.

Notes:

- desktop packaging config is prepared, but not yet build-verified on this machine
- the site is now updated to show `0.8` instead of stale `0.5` text mode copy

## `0.9` Floating Study Overlay System

Planned functions:

- floating Windows overlays
- always-on-top classroom layout
- separate desktop surfaces:
  - subtitle window
  - notes window
  - AI answer window
- lightweight classroom mode
- multi-monitor positioning support

Focus:
turn KonspektAI into a true realtime study copilot on Windows.

## After `0.9`

Planned functions:

- better summary generation
- improved flashcard quality
- optional PDF and DOCX templates
- local AI optimization
- multilingual cleanup
- study presets and classroom modes

Rule for future work:

if a stage description says something exists, the code and UI should reflect it before the next stage claims victory.
