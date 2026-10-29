---
name: openai-integration
description: Add or change OpenAI API calls (speech-to-text, chat, structured output, text-to-speech) in tutor/stt.py, tutor/llm.py, tutor/tts.py. Use when touching models, SDK parameters, error handling or costs.
---

# OpenAI integration

Background: [docs/guidelines/05-openai-structured-output.md](../../../docs/guidelines/05-openai-structured-output.md), [docs/guidelines/07-evaluation-and-security.md](../../../docs/guidelines/07-evaluation-and-security.md).

## Steps

1. Check current OpenAI docs (Context7: `openai` Python SDK) for the exact method, model names and parameters. Do not rely on memory.
2. Keep one client per process, created from `config.py`. Key from `.env` only, fail fast if missing.
3. Model names and the TTS voice come from config, never hardcoded in the function. No per-session voice or speed in the MVP.
4. Each wrapper is one small function with a clear signature:
   - `transcribe(audio_bytes, filename) -> str`
   - `reply(session, user_text) -> TutorTurn` (Pydantic: `reply`, `corrections`)
   - `summarize(session) -> Summary` (Pydantic, structured output, shape from the spec)
   - `synthesize(text) -> bytes` (mp3, voice from config)
5. Structured output: pass a Pydantic model, validate the result, retry a bounded number of times on validation failure.
6. Errors: catch API/network errors at the wrapper or endpoint boundary and return a clear message to the frontend. No silent fallbacks that hide failures.
7. Limits: set `max_tokens`/equivalent for chat, bounded retries, trim history before sending.
8. No sensitive data in logs or errors (see `.claude/rules/code-style.md` → "Logs and error messages"): never log prompts, learner text, profile values, headers or the key, and never pass `str(error)` of an OpenAI exception to the frontend. Log model, latency, token usage and the error type; write the user-facing message yourself.

## Check

- Run one real call manually (ask before running loops or batches).
- Confirm the frontend handles the error path (missing key, timeout, empty transcript).
