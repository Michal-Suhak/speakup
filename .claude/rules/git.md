# Git and pull requests

## General

- Commit, push and open PRs only when the user asks.
- Merge a PR only with the user's explicit permission for that PR ("merge PR #N"). Approval of one PR never covers another. Before merging, show the squash commit message and description (template below).
- **No attribution in commits or PRs:** no `Co-Authored-By` trailer, no "Generated with Claude Code", no session links. The commit author is the user only.
- Never commit `.env`, `local/`, `sessions/`, `profiles/`, `.venv/`, `__pycache__/` or audio files.
- Check `git status` and the diff before committing.

## Small changes, small PRs

- One PR = one reviewable change: one spec stage, one fix or one refactor. Never mix them.
- Aim for a diff a reviewer can read in about 15 minutes: roughly up to 300 changed lines of code (docs and lock files excluded). Bigger work is split into several PRs, each leaving `main` working.
- Large specs are delivered stage by stage (e.g. one PR per stage of `0001-mvp.md`), with the spec checklist ticked in each PR.
- Commits inside a PR are small and focused too; they are squashed on merge, so they serve the review, not the history.

## Flow

1. `main` only changes through PRs. Never commit directly to `main`.
2. Branch from an up-to-date `main`, one branch per PR.
3. Commit the work on the branch, then run `/code-review` on the branch diff (`main...HEAD`). Fix the findings with new commits, or explain in "Open points" why one is left as is. Never open a PR without this review.
4. Push the branch and open a PR to `main` with `gh pr create`, using `.github/pull_request_template.md`.
5. Review fixes go as new commits on the same branch, no force-push after the PR is opened unless the user asks.
6. PRs are always squash-merged, so the PR title becomes the single commit on `main`.
7. After merging: delete the branch (`--delete-branch`), switch to `main` and pull.

## Squash merge commit

The commit on `main` describes the final state of the PR, not its history (no "fix review comments", no intermediate steps).

```
<PR title> (#<PR number>)

- <Verb> <what changed> (<path or area>)
- <Verb> <what changed> (<path or area>)
```

- **Subject**: the PR title plus `(#N)`, imperative, ≤ 72 characters.
- **Description**: 2–6 bullets, one per meaningful change, each starting with an imperative verb (Add, Change, Fix, Remove), wrapped at 72 characters. Mention the spec number when the PR implements one.
- No attribution, no links to sessions, no checklist, no "How to test".

Example:

```
Add session history (0002) (#7)

- Save finished sessions as JSON in sessions/ (tutor/history.py)
- Add GET /api/history and a history screen in the start view
- Update 0002 spec: stage 1 done, decision on file-per-session
```

Merge command:

```bash
gh pr merge <N> --squash --delete-branch --subject "<subject>" --body "<description>"
```

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
- **Changes**: only what this PR changes (`git diff main...HEAD --stat`), never a tour of the repo. One line per changed file or module saying *what changed in it*, not what the file is for. Use only the template groups (Backend, Frontend, Prompts, Docs and config) and drop empty ones. Many similar files (e.g. a renamed folder) go in one line.
- **How to test**: exact steps to run and verify. For PRs without runtime changes (docs, specs, `.claude/`, config) write "Not applicable: no runtime changes." instead of inventing steps.
- **Checklist**: Claude's responsibility, not the reviewer's. Before opening or updating the PR, check every item against the diff and tick it when it holds. An item that the diff cannot violate (e.g. no Python code, so no prompt text in Python) holds and is ticked. An item that does not hold stays unticked and must be fixed before asking for review, or explained in "Open points".
- **Open points**: only what genuinely needs the reviewer's decision, known limitations and follow-ups, or "None". Resolve inconsistencies you find before opening the PR instead of listing them here.

Keep it factual: no marketing language, no AI attribution, no repeated content from the spec beyond a link.
