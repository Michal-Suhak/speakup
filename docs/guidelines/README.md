# Guidelines: agentic English-learning app (OpenAI + TTS)

General principles for building a language-tutor agent.

This is background knowledge, not project scope. Concrete decisions for SpeakUp (stack, repo structure, JSON formats, stages) live in the [specs](../specs/README.md) and take precedence over these guidelines. Directory structures and schemas shown here are a pattern for a more mature version, not the MVP plan.

## Files

| File | Topic |
|------|-------|
| [01-architecture.md](01-architecture.md) | "Text core" pipeline, project structure, request flow |
| [02-context-and-prompts.md](02-context-and-prompts.md) | Prompts as code: Jinja2, XML tags, context hygiene |
| [03-memory.md](03-memory.md) | Memory layers, episode compression, persistence |
| [04-pedagogy-and-session.md](04-pedagogy-and-session.md) | Point A → B, session phases, correction policy, skills |
| [05-openai-structured-output.md](05-openai-structured-output.md) | Pydantic, Instructor, schema-guided reasoning |
| [06-voice-tts-stt.md](06-voice-tts-stt.md) | TTS/STT, latency, voice control |
| [07-evaluation-and-security.md](07-evaluation-and-security.md) | Leaderboard, LLM-as-judge, simulator, privacy, costs |

## 10 rules in short

1. **Domain first, code second.** Start by writing out dialogues and the session state diagram. The happy path is 10–30% of reality.
2. **Text is the core.** Voice → STT → text → LLM + logic → text → TTS → voice. All logic, validation and memory work on text.
3. **The LLM decides, Python executes.** The model picks intent or content; deterministic code does routing, state writes and API calls.
4. **State drives routing.** Which skill runs is decided by a state machine (session phase), not by asking the LLM.
5. **Prompts are code.** Jinja2 templates live in git; render and inspect them *before* sending to the API.
6. **Every LLM answer has a schema.** Pydantic and structured output, with a `thinking` field before the answer field.
7. **Memory is selection, not collection.** The context gets a compressed essence (facts, mistakes, next step), never raw logs.
8. **Teach communication, not textbook grammar.** The goal is "Sorry, I didn't catch that", not "I do not understand what you are saying".
9. **Measure, don't guess.** Your own leaderboard of binary checks instead of vibe checks and public rankings.
10. **Autonomy needs safeguards.** Iteration and token limits, secrets in env, pseudonymise personal data before sending it to the cloud.
