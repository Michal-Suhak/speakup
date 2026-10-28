# NNNN – Change title

| Field | Value |
|---|---|
| Status | `draft` |
| Created | YYYY-MM-DD |
| Last updated | YYYY-MM-DD |
| Depends on | [0001](0001-mvp.md) |
| Supersedes | – |

## 1. Problem and context

What doesn't work or is missing, from the learner's perspective. Why now. 2–5 sentences.

## 2. Goal

One sentence: what the learner will be able to do after this ships.

## 3. Scope

**In scope:**
- …

**Out of scope:**
- …

## 4. User scenarios

Step-by-step flow from the learner's perspective. Happy path and edge cases (silence, wrong answer, API error, Polish instead of English…).

1. …

## 5. Solution design

Fill in only the subsections this change touches, delete the rest.

### Architecture and flow
Which modules change (`app.py`, `tutor/*.py`, `static/*`), the new data flow.

### Data and formats
New or changed JSON (model response, profile, summary, session state). Full example.

### Endpoints
| Method | Path | Input → output |
|---|---|---|

### Prompts
Changes in `prompts/*.md`: what we add to the tutor's behaviour and why.

### Interface
What the learner sees and clicks, UI states, error messages.

## 6. Decisions

| Decision | Choice | Alternatives | Why |
|---|---|---|---|

## 7. Cost, latency, privacy

- Additional OpenAI calls per turn or session and estimated cost.
- Impact on latency.
- Which user data is stored, where and for how long.

## 8. Risks and open questions

- [ ] …

## 9. Implementation plan

Small, testable steps in order. Each ends with something runnable.

- [ ] …

## 10. Acceptance criteria

Binary (yes/no), checkable manually or by a test.

- [ ] …

## 11. Tests and evaluation

How we check quality: unit tests, manual scenarios, tutor checks (`tutor-eval`).

## Changelog

| Date | Change |
|---|---|
| YYYY-MM-DD | Document created. |
