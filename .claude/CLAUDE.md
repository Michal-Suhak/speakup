# SpeakUp

Local app for practising spoken English with a voice tutor. User speaks (push-to-talk), backend runs OpenAI STT → chat → TTS, browser plays the answer and shows the transcript. Target user: Polish learner, levels A1–C2 (default A2/B1), learner profiles in `profiles/`.

- Scope lives in `docs/specs/` (live documentation). MVP: `docs/specs/0001-mvp.md`. Every new feature starts as a spec there (skill `feature-spec`), code follows the accepted spec, and the spec is updated together with the code.
- Background guidelines: [docs/guidelines/](../docs/guidelines/README.md) (architecture, prompts, memory, pedagogy, structured output, voice, evals). Read the relevant file before designing a new area.
- `local/` is private and gitignored: never commit it and never reference it from tracked files. Anything needed by the project goes to `docs/`.

## Stack

Python 3.11+, FastAPI, uvicorn, `openai` SDK, `python-dotenv`. Frontend: plain HTML/CSS/JS, `MediaRecorder`. No frontend framework, no build step.

## Rules

Project rules live in `.claude/rules/`:

- `approach.md` – how to design and solve things in this project
- `boundaries.md` – what is allowed, what needs asking, what is off limits
- `code-style.md` – how code is written (including: no unnecessary comments)
- `git.md` – commits (no Co-Authored-By or any AI attribution)
- `docs.md` – specs workflow and keeping docs in sync with code

Project skills live in `.claude/skills/`: `feature-spec`, `tutor-prompt`, `openai-integration`, `voice-pipeline`, `tutor-eval`.

## Commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```
