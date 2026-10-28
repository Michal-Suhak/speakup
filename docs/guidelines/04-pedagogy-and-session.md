# 04. Pedagogy, session and skills

## Product goal: a communication coach, not a comma checker

The tutor should close the gap between textbook English and real-life English:

| Situation | Textbook 🤖 | Real life 🗣️ |
|---|---|---|
| Booking | "I would like to reserve a table for two people for 7 PM." | "Hi, can I get a table for two at seven?" |
| Greeting | "How are you doing today?" / "I am fine, thank you." | "How's it going?" / "Good, you?" |
| Not understanding | "I do not understand what you are saying." | "Sorry, I didn't catch that." |

The learner should understand native speakers and sound natural, not like "robot language".

## A marathon, not a transaction

A table booking has an end: *Done*. Learning lasts weeks, and success is a change in the learner's head, not a delivered answer. That's why the tutor is **stateful** and **Socratic**: it doesn't hand out answers, it guides.

## Point A → Point B (gap analysis)

1. **Point A**: current state ("I understand but can't speak", level B1).
2. **Point B**: SMART goal ("20-minute pitch in NY without notes by 2026-06-01", success criteria as a list).
3. **Delta → plan**: milestones delivered across sessions. A delta that is too large ("from zero to native") means the goal must be renegotiated.

Each step is a separate skill (`point_a`, `point_b`, `plan`) that collects data over several turns until the required fields are filled (`point_a_done = True`).

## Anatomy of a session (workflow phases)

| Phase | Agent's task |
|---|---|
| `HOMEWORK_CHECK` | Check homework. Do not start a new topic. |
| `TOPIC_INTRODUCTION` | Introduce the topic, refer to facts from episodic memory. |
| `PRACTICE` | Roleplay or conversation simulation, watch for recurring mistakes. |
| `FEEDBACK_WRAPUP` | Wins / gaps, comparison with previous sessions, homework. |

Phase transitions are done by code (state machine). The LLM can at most *signal* readiness (e.g. a `ready_for_next_phase: bool` field in the schema), but Python makes the decision.

## Personalisation

- **Correction policy**: `GENTLE` corrects only mistakes that block understanding, `STRICT` corrects everything (grammar, tone, pronunciation). The switch lives in the template (`{% if %}`).
- **Learning style**: `IMMERSIVE` (conversation), `ANALYTICAL` (rules), `VISUAL`.
- **Rapport**: personal facts from episodic memory ("How's Luna?").
- **Knowledge tracing**: `skills[rule].mastery` and `last_practiced`, the basis for spaced repetition.

## Skills (procedural memory)

- **A skill is a recipe, not a cook.** It declares `name`, `output_model` (Pydantic) and `template` (.j2), but doesn't call the API. The agent executes it.
- A shared interface lets you add skills without changing agent code.
- **Avoid the "God Agent"** with one giant prompt. Splitting into skills solves semantic overload.
- Skill candidates: `onboarding (point_a)`, `goal (point_b)`, `plan`, `roleplay`, `correction`, `vocab_drill`, `homework_check`, `session_summary`.

```python
def decide_next_action(state) -> str:
    wf = state.workflow
    if not wf.point_a_done: return "point_a"
    if not wf.point_b_done: return "point_b"
    if not wf.plan_done:    return "plan"
    return PHASE_TO_SKILL[wf.phase]
```

## Autonomy: only as much as needed

A tutor is mostly at the "stateful + skills" level. A ReAct loop, planning and tools (MCP) are only useful for external actions (dictionary API, review calendar, search). Then:

- force one action from a closed set (`Union[...]` with a discriminator),
- treat the plan as a hypothesis: execute one step and re-plan,
- filter the tool list before injecting it into context (discovery before execution),
- hard iteration limit (e.g. max 10).
