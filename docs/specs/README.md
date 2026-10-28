# Specs

Live documentation of the project. Every functional change starts with a document here, and the document is updated during and after implementation, so it always describes what is in the code.

## How it works

1. **Idea**: we discuss the change in a conversation with Claude.
2. **Spec**: Claude creates the document with the `feature-spec` skill (from the [template](_template.md)) with status `draft` and adds it to the index below.
3. **Acceptance**: we resolve the open questions. When none are left, the status changes to `accepted`.
4. **Implementation**: status `in-progress`, the checklist in "Implementation plan" is ticked as work progresses. Every decision made along the way goes into "Decisions" and "Changelog".
5. **Closing**: status `done` once the acceptance criteria are met.

Code never gets ahead of the document: if the implementation differs from the spec, we fix the document first.

## Statuses

| Status | Meaning |
|---|---|
| `draft` | Idea described, open questions remain, nothing is implemented. |
| `accepted` | Agreed, ready for implementation. |
| `in-progress` | Being implemented. |
| `done` | Implemented and verified against the acceptance criteria. |
| `rejected` | Rejected (kept for history, with the reason). |
| `superseded` | Replaced by another document (link in the metadata). |

## Naming

`NNNN-short-name.md`: next 4-digit number and a kebab-case name, e.g. `0002-session-history.md`. Numbers are never reused.

## Index

| No. | Document | Status | Description |
|---|---|---|---|
| 0001 | [MVP: voice English tutor](0001-mvp.md) | `in-progress` | STT → chat → TTS loop, profiles, corrections, session summary. |
