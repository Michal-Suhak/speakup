# Approach

## Order of work

1. Work stage by stage from `docs/specs/0001-mvp.md`. Finish the current stage, show how to run it, stop. Do not build stage 2/3 features early.
2. Before coding a new flow, write down the dialogue and states it must handle (happy path is 10–30% of reality: silence, too-short recording, Polish answer, off-topic, API error).
3. Pick the smallest solution that works: stdlib → already installed dependency → a few lines of code. New dependency only with a clear reason, ask first.

## Architecture principles

- **Text core.** Voice → STT → text → LLM → text → TTS → voice. All logic, validation and state work on text. No audio-to-audio / Realtime API before the plan says so.
- **LLM decides content, Python decides flow.** Session phase, routing, retries, limits and state writes are plain code. Never ask the LLM "what should the app do next" when an `if` can answer.
- **Prompts are code.** They live in `prompts/`, are versioned in git and rendered with session data. Render and inspect a prompt before blaming the model.
- **Structured output for every model answer consumed by code**: each turn returns `reply` (spoken, English) + `corrections` (shown on screen, `explanation_pl`); the summary is JSON too. Pydantic model as `response_format`, validate, bounded retry on failure. No parsing of free text.
- **Build in layers**: text conversation first, then STT, then TTS. Each layer testable on its own.
- **Context is selected, not collected.** Send only what the turn needs: system prompt, settings, recent messages. Summarise or trim long history instead of sending everything.
- **Thin wrappers.** `stt.py`, `llm.py`, `tts.py` are small functions over the SDK, so providers and models can be swapped via config.
- **State is explicit.** Session state is a typed object (topic, level, history). Use `Field(default_factory=list)` for mutable defaults.

## Tutor behaviour (product rules)

- Communication coach, not grammar police: natural "real life" English over textbook phrasing.
- Short replies (2–4 sentences), end with a question, user talks more than the tutor.
- Correct only important mistakes: recast the correct form naturally inside `reply`, put the Polish explanation into `corrections` (screen only). The tutor's voice stays English.
- Topics and level come from the learner profile (`profiles/*.json`), not a fixed list.
- Reply text must be TTS-friendly: no markdown, emoji, lists, brackets.

## When unsure

- Model names, SDK parameters, pricing: check current OpenAI docs (Context7), do not rely on memory.
- Scope or product decision not covered by the plan: ask, do not guess.
