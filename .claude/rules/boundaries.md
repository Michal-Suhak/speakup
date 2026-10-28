# Boundaries

## Allowed without asking

- Editing and creating files inside the repo for the current stage of `docs/specs/0001-mvp.md`.
- Creating `draft` specs and keeping specs in `docs/specs/` in sync with the code.
- Running the app locally, running tests and quick checks.
- Reading `docs/specs/0001-mvp.md` and `docs/guidelines/`.

## Ask first

- Moving a spec to `accepted`, `done`, `rejected` or changing the MVP scope.
- Implementing anything that has no `accepted` spec (except bug fixes and refactors without behaviour change).
- Adding a dependency (`uv add`).
- Changing the stack (framework, frontend library, database, Realtime API).
- Changing public endpoints, the turn JSON (`reply` + `corrections`), the summary JSON or the profile format.
- Changing OpenAI models in config (cost impact).
- Anything that calls the OpenAI API in a loop or batch (evals, simulations) – state the expected number of calls first.
- Committing, pushing, creating branches or PRs.
- Deleting files that were not created in the current task.

## Never

- Put the API key, or any secret, in code, logs, frontend, prompts or commits. Keys come only from `.env`.
- Call OpenAI from the browser. All API calls go through the backend.
- Commit `.env`, `local/`, `sessions/`, `profiles/`, recordings or other user data.
- Store user voice recordings longer than needed for the current request, unless a stage explicitly requires it.
- Treat user speech, transcripts, the custom topic or profile fields as instructions to the system. They are data inside the prompt (`<learner_profile>` section), validated and length-limited.
- Add Co-Authored-By, "Generated with Claude Code" or any other AI attribution to commits or PRs.
- Hardcode model names or voice ids in logic. They belong in `config.py` / `.env`.
- Add unbounded loops around the LLM. Every retry or agent loop has a hard limit.
