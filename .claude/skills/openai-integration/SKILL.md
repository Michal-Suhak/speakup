---
name: openai-integration
description: Add or change OpenAI API calls (speech-to-text, chat, structured output, text-to-speech) in tutor/stt.py, tutor/llm.py, tutor/tts.py. Use when touching models, SDK parameters, error handling or costs.
---

# OpenAI integration

Background: [docs/guidelines/05-openai-structured-output.md](../../../docs/guidelines/05-openai-structured-output.md), [docs/guidelines/07-evaluation-and-security.md](../../../docs/guidelines/07-evaluation-and-security.md).

## Steps

1. Check current OpenAI docs (Context7: `openai` Python SDK) for the exact method, model names and parameters. Do not rely on memory.
2. Keep one client per process, created from `config.py`. Key from `.env` only, fail fast if missing.
3. Model names, voice and speed come from config, never hardcoded in the function.
4. Each wrapper is one small function with a clear signature:
   - `transcribe(audio_bytes, filename) -> str`
   - `reply(history, user_text, settings) -> TutorTurn` (Pydantic: `reply`, `corrections`)
   - `summarize(history) -> Summary` (Pydantic, structured output)
   - `synthesize(text, voice, speed) -> bytes`
5. Structured output: pass a Pydantic model, validate the result, retry a bounded number of times on validation failure.
6. Errors: catch API/network errors at the wrapper or endpoint boundary and return a clear message to the frontend. No silent fallbacks that hide failures.
7. Limits: set `max_tokens`/equivalent for chat, bounded retries, trim history before sending.
8. Do not log full prompts with user data or the API key. Log model, latency and token usage instead.

## Check

- Run one real call manually (ask before running loops or batches).
- Confirm the frontend handles the error path (missing key, timeout, empty transcript).
