# Code style

## General

- Simple and readable over clever. No abstractions without a second use case: no base classes with one subclass, no factories, no config for values that never change.
- Fewest files that keep responsibilities clear. Follow the structure in `docs/specs/0001-mvp.md`.
- Layers: `app.py` only creates the app (routers, error handlers, static files); endpoints live in `api/<area>.py` as an `APIRouter` and stay thin (parse request, call `tutor/`, map the result); domain logic lives in `tutor/` and never imports FastAPI. Domain errors are mapped to HTTP status codes by exception handlers in `app.py`.
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

## Logs and error messages

Anything logged or returned in an error can leak (terminal history, screenshots, issues, PRs), so it carries no sensitive data.

- **Never include:** the API key or any secret, request headers, full prompts, learner messages or transcripts, profile field values, audio, raw OpenAI error bodies or `str(error)` of provider exceptions, `repr()` of whole models or sessions.
- **Allowed:** ids, file names, error types (`type(error).__name__`), HTTP status codes, model names, durations, token and character counts.
- Error messages for the frontend are written by us: short, actionable, in English, e.g. "OpenAI request failed (APITimeoutError). Try again in a moment." Never forward a library's message as is.
- Chain the original exception (`raise ... from error`) instead of putting its text in the message; for pydantic errors, report the field name and error type, not the input value (`ValidationError` text contains the input).
- When adding a log line, check it against this list as if it were posted publicly.

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
