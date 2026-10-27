# Git

- Commit only when the user asks.
- **No attribution in commits or PRs:** no `Co-Authored-By` trailer, no "Generated with Claude Code", no session links. The commit author is the user only.
- Commit messages in English, imperative mood, short subject (≤ 72 chars), body only when the *why* is not obvious.
- One logical change per commit. Do not mix refactors with features.
- Never commit `.env`, `local/`, `sessions/`, `.venv/`, `__pycache__/` or audio files.
- Check `git status` and the diff before committing.
