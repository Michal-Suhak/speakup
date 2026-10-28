# Code style

## General

- Simple and readable over clever. No abstractions without a second use case: no base classes with one subclass, no factories, no config for values that never change.
- Fewest files that keep responsibilities clear. Follow the structure in `docs/specs/0001-mvp.md`.
- Names, code, comments and log messages in English. Docs in `docs/` and the README in English. User-facing UI text in Polish.
- Match the surrounding code: naming, idioms, error handling.

## Comments

- **No unnecessary comments.** Do not comment what the code already says, do not narrate steps, do not leave "changed X" / "new" / "TODO maybe" notes, do not add section banners.
- Write a comment only when it explains *why* something non-obvious is done (a workaround, an API quirk, a deliberate limit).
- Docstrings only on functions whose behaviour is not obvious from name and types. One line is usually enough.

## Python

- Python 3.11+, type hints on public functions, `X | None` instead of `Optional[X]`.
- Dependencies only through uv: `uv add` / `uv remove`, commit `pyproject.toml` and `uv.lock` together, run scripts and tests with `uv run`. No `pip install`, no `requirements.txt`.
- Pydantic models for structured LLM output and session state. `Field(default_factory=...)` for lists and dicts.
- One OpenAI client per process, created in one place.
- Config through `config.py` reading `.env`. Fail fast with a clear message when the key is missing.
- Handle errors at boundaries (endpoints, API calls): return a clear error to the frontend, do not swallow exceptions silently.
- f-strings for code; prompt text lives in `prompts/`, not in Python strings.

## Frontend

- Plain HTML/CSS/JS, no framework, no build step.
- Small functions, `async/await` with `fetch`, visible UI states: listening / processing / speaking / error.
- Show user-friendly messages for: no microphone, network error, empty or too short recording.

## Prompts

- Prompt files in `prompts/`, English instructions, clear sections (role, rules, current settings).
- Placeholders use `$name` syntax rendered with `string.Template.substitute` (never `str.format`, which breaks on literal braces). Lists are joined with ", ", empty values render as "none". Switch to Jinja2 only when conditional logic is really needed.

## Tests

- Tests use pytest (`uv run pytest`), files in `tests/test_*.py`. Non-trivial logic (state updates, parsing, validation) and every endpoint get tests; prefer plain functions, `parametrize`, and built-in fixtures (`tmp_path`, `monkeypatch`).
- Endpoints are tested through `fastapi.testclient.TestClient`, so status codes and error messages are checked as the frontend sees them.
- Do not hit the real OpenAI API in unit tests; test prompt rendering and parsing with fixed inputs.
