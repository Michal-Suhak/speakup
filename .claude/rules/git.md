# Git and pull requests

## General

- Commit, push and open PRs only when the user asks. Never merge; the user reviews and merges.
- **No attribution in commits or PRs:** no `Co-Authored-By` trailer, no "Generated with Claude Code", no session links. The commit author is the user only.
- Never commit `.env`, `local/`, `sessions/`, `.venv/`, `__pycache__/` or audio files.
- Check `git status` and the diff before committing.

## Flow

1. `main` only changes through PRs. Never commit directly to `main`.
2. Branch from an up-to-date `main`, one branch per spec or fix.
3. Commit, push the branch, open a PR to `main` with `gh pr create`, using `.github/pull_request_template.md`.
4. Review fixes go as new commits on the same branch, no force-push after the PR is opened unless the user asks.
5. PRs are squash-merged, so the PR title becomes the commit on `main`.

## Branch names

`<type>/<short-kebab-name>`, English, lowercase.

| Type | Use for | Example |
|---|---|---|
| `feat` | New behaviour from a spec (include the spec number) | `feat/0002-session-history` |
| `fix` | Bug fix | `fix/safari-mp4-upload` |
| `refactor` | Code change without behaviour change | `refactor/split-llm-module` |
| `docs` | Specs, guidelines, README only | `docs/0003-roleplay-spec` |
| `chore` | Config, dependencies, tooling, `.claude/` | `chore/pr-template` |
| `test` | Tests and evals only | `test/tutor-eval-checks` |

## Commit messages

- English, imperative mood, capitalised, no trailing period: `Add session history endpoint`.
- Subject ≤ 72 characters, no type prefix.
- Body only when the *why* is not obvious; wrap at 72 characters.
- One logical change per commit. Do not mix refactors with features.

## PR title

- Same style as a commit subject: imperative, ≤ 72 characters, no type prefix.
- For spec work add the spec number at the end: `Add session history (0002)`.

## PR description

Always fill `.github/pull_request_template.md`:

- **Summary**: 1–3 sentences, what changes and why.
- **Spec**: link to `docs/specs/NNNN-*.md`, or "None" for fixes and refactors.
- **Changes**: grouped by area (Backend, Frontend, Prompts, Docs and config), one line per file or module; drop empty groups.
- **How to test**: exact steps to run and verify.
- **Checklist**: tick only what is true; leave unticked items visible and explain them in "Open points".
- **Open points**: decisions for the reviewer, known limitations, follow-ups, or "None".

Keep it factual: no marketing language, no AI attribution, no repeated content from the spec beyond a link.
