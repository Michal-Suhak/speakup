---
name: feature-spec
description: Create or update a feature specification in docs/specs/ (live documentation). Use when the user wants to add, change or discuss a feature, when a spec's status changes, or when implementation deviates from a spec.
---

# Feature spec

Specs in `docs/specs/` are the live documentation of SpeakUp. Process and statuses: `docs/specs/README.md`. Template: `docs/specs/_template.md`. Background knowledge: [docs/guidelines/](../../../docs/guidelines/README.md).

## Creating a new spec

1. Talk first. Before writing, make sure you know: the learner problem, the goal, what is out of scope. Ask about anything missing; do not invent product decisions.
2. Pick the next number: highest `NNNN` in `docs/specs/` + 1. File name `NNNN-kebab-name.md`.
3. Copy `_template.md`, fill the metadata: status `draft`, today's date in both date fields, dependencies (at least `0001-mvp.md` if it builds on the MVP).
4. Fill the sections from the conversation:
   - write in English; only learner-facing strings quoted from the UI (and `*_pl` example values) stay in Polish,
   - in "Solution design" keep only the subsections the change touches,
   - give full JSON examples for any new or changed format,
   - "Decisions" lists real alternatives and the reason for the choice,
   - "Cost, latency, privacy" is never empty when OpenAI calls or stored user data change, and says what the feature logs and returns in errors (only ids, error types, counts; see `.claude/rules/code-style.md` → "Logs and error messages"),
   - "Implementation plan" uses small steps, each ending in something runnable,
   - "Acceptance criteria" are binary and checkable.
5. Unknowns go to "Risks and open questions" as checkboxes, not into guesses in the design.
6. Check against `.claude/rules/` (boundaries, approach) and existing specs. If it conflicts with an accepted spec, say so and record it in "Depends on" / "Supersedes".
7. Add a row to the index in `docs/specs/README.md`. If the spec comes from `docs/backlog.md`, remove that item there.
8. Show the user a short summary and the open questions. Do not start implementing a `draft`.

## Updating a spec

- Status change: update the metadata table, "Last updated", the index row in `README.md` and add a "Changelog" row.
- `draft` → `accepted` only when the user agrees and there are no open questions left.
- During implementation (`in-progress`): tick checklist items as they are done; a decision made while coding goes into "Decisions" and "Changelog" in the same change as the code.
- If the code has to differ from the spec, update the spec first, then the code.
- `done` only when every acceptance criterion is ticked.
- Never delete rejected or superseded specs; set the status and give the reason or the link.

## Do not

- Do not write code inside a spec beyond short examples of formats, signatures or prompts.
- Do not copy the background guidelines into a spec; link to the relevant file in `docs/guidelines/` instead.
- Do not change `0001-mvp.md` scope silently; MVP changes get a "Changelog" row or a new spec.
