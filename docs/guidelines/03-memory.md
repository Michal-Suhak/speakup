# 03. Memory

The agent does not "learn" by training weights. "Training" means managing what the agent knows about the learner. Even the best model without memory is an intelligent amnesiac.

## Layers

| Layer | What it holds (tutor) | Rate of change |
|---|---|---|
| 🏛️ **Core** | Identity, role, prime directives | Almost never |
| 🧠 **Semantic** | Profile: language, level, SMART goal, learning style, correction policy, skill map (`mastery`, `last_practiced`) | Per session |
| 📚 **Episodic** | Compressed sessions: summary, personal facts, mistakes, recommendation | After each session |
| 🎯 **Workflow** | Session phase, milestone, homework, `*_done` flags | Per turn |
| ⚡ **Working** | Recent messages, scratchpad (`thinking`), tool results, API errors | Per turn |
| 🛠️ **Procedural** | Skills (prompt + schema) | On deploy |
| 🔧 **Resource** | API status, token budget, available tools | Runtime |

Not every app needs every layer. The choice is deliberate, but a missing layer causes a predictable bug: without episodic memory the agent forgets yesterday's mistakes, without workflow it gets lost within a session.

## Schemas (Pydantic)

```python
class StudentProfile(BaseModel):
    name: str
    native_lang: str
    target_lang: str
    goal: LearningGoal                      # statement, target_level, deadline, success_criteria
    style: LearningStyle = LearningStyle.IMMERSIVE
    policy: CorrectionPolicy = CorrectionPolicy.GENTLE
    skills: dict[str, SkillState] = Field(default_factory=dict)
    history: list[EpisodeMemory] = Field(default_factory=list)
```

**Always use `Field(default_factory=...)` for lists and dicts.** A mutable default `= {}` or `= []` risks sharing data between learners.

## Episode compression (ETL for AI)

After the session, asynchronously, turn the raw log into a structure:

```python
class MistakeLog(BaseModel):
    user_phrase: str        # "I thinked"
    correction: str         # "I thought"
    grammar_rule: str       # "Past Simple Irregular"

class EpisodeMemory(BaseModel):
    summary: str
    personal_facts: list[str]          # "Has a cat named Luna" → rapport in the next session
    mistakes: list[MistakeLog]         # knowledge tracing → what to practise
    next_step_recommendation: str
```

- The gain: 90–99% fewer tokens, memory of the relationship (cat, trip to NY) and hard data for analytics ("80% of your mistakes are irregular verbs").
- **This is lossy compression.** What isn't in the schema is lost. No field for mood? The learner's frustration disappears. Grow the schema iteratively.
- For accuracy you can run the same log through separate filters (didactic: mistakes only; relational: facts and mood). It costs more tokens, but runs in the background, so latency doesn't matter.
- Show only the last N episodes in the prompt (e.g. `profile.history[-3:]`). `MemoryManager.cleanup(max_episodes=...)` trims the rest.

## Session loop

```
Session start → load profile + recent episodes → session → compression → save → (next session)
```

The result of one session (homework, mistakes, assessment) is the input of the next. This is where a chatbot becomes a tutor.

## Where to keep data

- To start: **a relational database (Postgres/SQLite) + JSON with Pydantic state**. That's enough.
- A vector database is not the default. Without metadata filters "everything is similar". Keyword search + LLM reranking often works better.
- Redis only as a cache or for ephemeral data. Everything important goes to a persistent database.
