# 02. Context and prompts

## Prompts are code

- Keep templates in `.j2` files in git. Avoid f-strings glued together in Python and external prompt platforms: Jinja2 + git is boring but stable for years.
- Conditional logic (correction policy, session phase) lives in the template, not in Python `if`s that concatenate text.
- Render state with `template.render(**state.model_dump())`, so templates can use `{{ profile.name }}`.
- **Render dry before calling the API.** Before debugging an answer, look at exactly what the model received.

## Prompt structure

Mark sections with XML tags, so the model can tell identity, context and instruction apart:

```jinja
{% include 'core.j2' %}       {# <core_memory>: identity, prime directives #}
{% include 'semantic.j2' %}   {# <student_context>: profile, goal, correction policy #}
{% include 'episodic.j2' %}   {# <episodic_memory>: facts, recent mistakes, next step #}
{% include 'working.j2' %}    {# <session_state>: phase + <active_instruction> #}

PROCESSING PRIORITY:
1. <active_instruction>  2. <episodic_memory>  3. <correction_settings>  4. <mission_objective>
```

- `core` holds the name, role, `creator_name` and rules that must not be broken (e.g. `NO_HOMEWORK_SOLVING`, `COMMUNICATION_FIRST`). State the identity rule explicitly, so the agent doesn't introduce itself as "an OpenAI model".
- Write instructions and tags in English, even when the learner speaks Polish: models follow English instructions better.
- Identifiers instead of descriptions (e.g. `PT-001`) help the model keep attention on a specific item and make errors easier to trace.

## Context hygiene: 4 sources of hallucination

| Problem | Symptom | Cause |
|---|---|---|
| **Poisoning** | Agent repeats a false fact | A system bug wrote junk into memory, or prompt injection from the user |
| **Distraction** | Copies old patterns instead of thinking | History too long, no summaries (effective threshold around 32k tokens) |
| **Confusion** | Gets lost among options | Too many tools or irrelevant documents in context |
| **Clash** | Contradictory behaviour | Memory says one thing, a tool result says another |

## Selection rules

- **Sculptor, not collector.** The context gets only what *this* turn needs.

| Always | Often | Rarely |
|---|---|---|
| Core, current phase, key facts about the learner | Last 5–10 messages, scratchpad from the previous turn | Old history, all past mistakes, full logs |

- Start with a **sliding window**. Add **summarisation** when you see the learner "losing" the thread.
- When a checklist in the prompt ("before answering check X, Y, Z") doesn't help, use **blinkers**: physically cut sections of the template that are not needed in the current phase. *What the model doesn't see can't distract it.*
- Watch out for **duplicated history**. If history is pasted into the system prompt, don't also send it in `messages`. Pick one source.
