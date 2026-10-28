---
name: voice-pipeline
description: Work on the voice loop – recording in the browser (MediaRecorder, push-to-talk), sending audio to /api/turn, transcription, TTS playback and UI states. Use for latency, audio format, recording or playback issues.
---

# Voice pipeline

Background: [docs/guidelines/06-voice-tts-stt.md](../../../docs/guidelines/06-voice-tts-stt.md), [docs/guidelines/01-architecture.md](../../../docs/guidelines/01-architecture.md).

## Flow

```
hold space / button → MediaRecorder → POST /api/turn (multipart) → STT → chat → TTS → JSON {user_text, reply, corrections, audio} → play + transcript
```

## Rules

- Text is the core: every turn produces `user_text` and `reply`; audio is only the interface.
- UI always shows one state: idle / listening / processing / speaking / error. Block a new recording while processing.
- Reject recordings that are too short or silent before calling STT (save cost, show a friendly message).
- Keep audio in memory on the backend; do not write files to disk per turn.
- The tutor text sent to TTS must be plain (no markdown, emoji, brackets). If a display version and a speech version ever differ, keep them as two fields.
- Choose a low-latency TTS model and a clear native accent; the voice comes from config (`.env`), there is no per-session voice or speed in the MVP.
- STT may "fix" the learner's grammar. When corrections depend on the transcript, check that it keeps what was really said.
- Measure latency per stage (STT, chat, TTS) before optimising. Quality first, then speed.

## Check

- Test in Chrome and Safari (webm and mp4 recordings): mic permission denied, no mic, network error, very short recording, long recording.
- "Repeat" replays the last audio without a new API call.
