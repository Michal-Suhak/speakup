# 01. Architecture

## Pipeline: text core instead of audio-to-audio

```
Microphone → [VAD] → STT → text ─┐
                                 ▼
             state + templates → LLM (structured output) → validation → state write
                                 ▼
                          reply text → TTS → speaker
```

- **We choose text core.** End-to-end audio models (e.g. GPT-4o voice mode) can be faster, but they are black boxes: structured output, validation and control over logic are hard.
- "Premature optimization is the root of all evil": quality and controllability first, latency second.
- The voice layer must be swappable. When audio models get native structured output, you replace the interface and the agent logic stays.

## Two worlds in one repo

| Software 1.0 (deterministic) | Software 3.0 (agentic) |
|---|---|
| UI, auth, database, queues, APIs | Prompts (Jinja2), response schemas, skills, memory |
| Phase routing, state writes, limits | Content generation, extraction, evaluation |

The boundary between them should be visible in the directory structure. The LLM never executes actions directly: it returns data that code validates and executes (a `dispatch` function is the permissions layer).

## Project structure (target pattern)

```
app/
├── app.py                 # interface (Gradio/FastAPI to start with), input/output only
├── config.py              # model, paths, keys from env (python-dotenv)
├── engine/
│   ├── client.py          # one OpenAI client (singleton, e.g. @lru_cache) + instructor
│   ├── prompter.py        # renders the system prompt from templates + state
│   ├── tutor_agent.py     # process_message(), decide_next_action(), run_skill()
│   ├── handlers.py        # response handling: stream vs block
│   └── jobs.py            # post-session jobs (episode compression, cleanup)
├── memory/
│   ├── schemas/           # Pydantic: core, semantic, episodic, workflow, working, resources
│   ├── templates/         # Jinja2: how each layer looks in the prompt
│   └── logic/             # MemoryManager (update/merge/cleanup), EpisodeCompressor
├── skills/                # one skill = .py (output schema) + .j2 (prompt)
├── voice/                 # STT/TTS, swappable adapters
└── templates/main.j2      # main template, includes the layers
```

Don't create everything at once. For an MVP it is enough to hardcode the learner profile and build one skill; swapping it for `db.get_user()` later is a one-line change.

## Flow of one turn

1. **Input**: text or STT transcript goes to `TutorAgent.process_message()`.
2. **Decision**: `decide_next_action()` looks at `workflow.phase` and flags (`point_a_done` etc.) and picks a skill or a plain reply. An `if/else` decides, not the LLM.
3. **Prompt**: `SystemPrompter` renders `main.j2` with the current state.
4. **LLM**: call with `response_model=<skill schema>`.
5. **Validation**: Pydantic; on error, retry (`max_retries`).
6. **State write**: `MemoryManager.update_from_output()` updates semantic, workflow and working memory.
7. **Output**: text goes to the UI and to TTS.
8. **After the session (async)**: `PostSessionJob` compresses the conversation into `EpisodeMemory` and saves it.

## The most common silent bug

**LLM ↔ Python desync**: the model returns correct data, but the code doesn't save it (or saves it in the wrong place). For every state change write a small test: input (state + skill output) → expected state.

## Observability from day one

A debug view: under every reply an expandable **system prompt**, and next to it **live state** (JSON with `core`, `profile`, `session`, `last_thought`). Without it you debug blind.
