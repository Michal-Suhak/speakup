# Live documentation

- `docs/specs/` is the source of truth for scope. `0001-mvp.md` is the MVP; every later change has its own spec `NNNN-name.md`.
- New feature or behaviour change: spec first (skill `feature-spec`), code only after the spec is `accepted`.
- Post-MVP ideas go to `docs/backlog.md` as one-line items in English, even when the user gives them in Polish; when an item becomes a spec, remove it from the backlog in the same PR.
- Backlog changes go through PRs. Collect several new ideas into one `docs/update-backlog` branch and PR (title "Update backlog") instead of one PR per idea.
- Small fixes that do not change behaviour (bugs, refactors, typos) do not need a spec.
- Keep specs in sync with code in the same change: tick plan and acceptance checkboxes, record decisions and add a "Changelog" row.
- If code must differ from an accepted spec, update the spec first and tell the user.
- Keep the index in `docs/specs/README.md` current (number, title, status, one-line description).
