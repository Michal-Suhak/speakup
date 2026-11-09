# 0004 – Session history

| Field | Value |
|---|---|
| Status | `accepted` |
| Created | 2026-11-08 |
| Last updated | 2026-11-08 |
| Depends on | [0001](0001-mvp.md), [0003](0003-practice-modes.md) (hint pattern, session expiry) |
| Supersedes | – |

## 1. Problem and context

After "zakończ sesję" the learner sees a useful summary, but it disappears with the next conversation. There is no way to look back at last week's mistakes or words, or to see how often one practises. Later features (vocabulary review, recurring mistakes) need these past sessions as data ([03-memory](../guidelines/03-memory.md): episodic memory).

## 2. Goal

The learner can see a list of past conversations on the start screen and open the summary of any of them.

## 3. Scope

**In scope:**
- Saving every ended session as one JSON file per session in `sessions/<profile_id>/`: date, topic, scene, duration, cost and the summary (when there is one).
- Saving sessions removed by the idle cleanup from 0003 too (without a summary).
- "Poprzednie rozmowy" on the start screen: the last 10 for the selected profile, a click shows the saved summary.
- Deleting one entry from the list.

**Out of scope:**
- Saving the full transcript or audio.
- A progress screen (charts, totals per week), vocabulary review, recurring mistakes – later specs built on this data.
- Using past sessions in the tutor's prompt.
- A database: files are enough locally; the [online deployment draft](online-deployment.md) moves them to its database.

## 4. User scenarios

1. **Normal end:** the learner clicks "zakończ sesję", sees the summary as today. On the start screen "Poprzednie rozmowy" now shows "8 lis, 18:40 · Travel · 6 min". A click opens the same summary view, with the date in the heading and "wróć" instead of "nowa rozmowa".
2. **Left without summary:** "nowa rozmowa" or closing the tab ends the session without a summary. The list shows it with "bez podsumowania"; a click shows only the date, topic, time and cost.
3. **Expired session:** the idle cleanup removes a session; it appears in the list like scenario 2.
4. **Too short:** the learner never answered; the session is still saved and shows "bez podsumowania".
5. **Scene:** a scene session shows its Polish name, e.g. "W restauracji".
6. **Delete:** the learner clicks "usuń" next to an entry and confirms in the browser dialog „Usunąć tę rozmowę z historii?”. The file is deleted and the list refreshes.
7. **Another profile:** switching the profile shows only that profile's history.
8. **Broken file:** a history file that is not valid JSON is skipped and logged by file name; the rest of the list works.
9. **First use:** no history yet; the section is hidden.

## 5. Solution design

### Architecture and flow

- `tutor/history.py` – `save_session(session, summary)`, `list_sessions(profile_id, limit)`, `load_session(profile_id, session_id)`, `delete_session(profile_id, session_id)`; atomic write (temp file + `os.replace`) as in `tutor/profiles.py`; ids validated with the same pattern as profile ids before building a path.
- `api/sessions.py` – `end_session` calls `save_session` after the summary; `tutor/session.py` expiry calls it too.
- `api/history.py` – new router (below).
- `static/` – history list on the start screen, summary view reused for saved entries.
- `config.py` – `SESSIONS_DIR = BASE_DIR / "sessions"` (already in `.gitignore`).

### Data and formats

`sessions/michal/2026-11-08T18-40-12-3f9c2a.json`:

```json
{
  "id": "3f9c2a7e5b0d4c1a9e8f7d6c5b4a3921",
  "profile_id": "michal",
  "started_at": "2026-11-08T18:40:12+01:00",
  "ended_at": "2026-11-08T18:46:31+01:00",
  "ended_by": "summary",
  "topic": "At a restaurant",
  "scene": "restaurant",
  "level": "B1",
  "duration_seconds": 379,
  "turns": 7,
  "cost_usd": 0.0041,
  "summary": {
    "top_corrections": [
      {"you_said": "I want a bill", "better": "Could I get the bill, please?", "explanation_pl": "Grzeczna prośba brzmi naturalniej z «could»."}
    ],
    "useful_vocabulary": [
      {"word": "the bill", "meaning_pl": "rachunek", "example": "Could we have the bill, please?"}
    ],
    "strengths": ["Dobrze zadajesz pytania w restauracji."],
    "tip_pl": "Następnym razem spróbuj zamówić deser i zapytać o polecenie."
  }
}
```

- `ended_by`: `summary`, `left` (ended without a summary) or `expired`.
- `summary`: `null` when none was generated.
- `turns`: number of learner messages.
- The file name starts with the start time, so a name sort gives the order without reading every file.

### Endpoints

| Method | Path | Input → output |
|---|---|---|
| GET | `/api/profiles/{profile_id}/history` | → list of the last 10: `id`, `started_at`, `topic`, `scene`, `duration_seconds`, `cost_usd`, `has_summary` |
| GET | `/api/profiles/{profile_id}/history/{session_id}` | → the full record above; 404 if missing |
| DELETE | `/api/profiles/{profile_id}/history/{session_id}` | → 204; 404 if missing |

Invalid ids return 400 (same as profiles). An unknown profile returns an empty list.

### Interface

- Start screen, after the topic box: "Poprzednie rozmowy" with an (i): „Tu znajdziesz swoje ostatnie rozmowy. Kliknij, żeby zobaczyć podsumowanie.”
- Each row: date and time (Polish format), topic or scene name, minutes, "bez podsumowania" when needed, and a small "usuń".
- Saved summary view: heading "Rozmowa z 8 listopada, 18:40", the same sections as the summary, a "wróć" link.
- New JS strings in `TEXT`.

## 6. Decisions

| Decision | Choice | Alternatives | Why |
|---|---|---|---|
| Storage | One JSON file per session in `sessions/<profile_id>/` | SQLite; one file per profile | No dependency, matches profiles; one file per session means no rewriting a growing file and no lost history on a crash. |
| What is saved | Metadata and the structured summary | Full transcript | Less learner data on disk; the summary is the compressed episode that later features need. |
| Sessions without a summary | Saved with `summary: null` | Not saved | Practice time counts for progress even when the learner skipped the summary. |
| List length | Last 10 | Paging | Enough for the start screen; the files stay for later features. |
| Delete | Per entry, with a browser `confirm()` | No delete; delete all | The learner controls their data; a custom dialog is not worth it for one action. |
| Retention | Keep until deleted | Automatic deletion after N days | Local, small files (~2 KB each); revisit for online deployment. |

## 7. Cost, latency, privacy

- **OpenAI calls:** none added; the summary is already generated.
- **Latency:** one small file write at the end of a session.
- **Privacy:** stores per learner: dates, topics, cost and the summary, which quotes short fragments of the learner's sentences. Local only, in the gitignored `sessions/`; deletable per entry. Logs contain only file names and error types, never summary content.

## 8. Risks and open questions

- [x] Time zone: saved with the server's offset and shown as saved (one machine locally).
- [x] Deleting all history of a profile at once: not now; per-entry delete only.

## 9. Implementation plan

**Stage 1 – saving**
- [ ] `tutor/history.py` with save, list, load, delete.
- [ ] Save on end (summary and left) and on expiry.
- [ ] Tests: file content, `ended_by`, atomic write, broken file skipped, invalid ids rejected.

**Stage 2 – viewing and deleting**
- [ ] `api/history.py` endpoints.
- [ ] Start screen list, saved summary view, delete with confirm, hint.
- [ ] Endpoint tests through `TestClient`.
- [ ] Manual check: end with summary, leave, delete, switch profile.

## 10. Acceptance criteria

- [ ] Ending a session with or without a summary, and an expired session, each create one file with the format above.
- [ ] The start screen lists the last 10 sessions of the selected profile, newest first, and hides the section when there are none.
- [ ] Clicking an entry shows its saved summary or the "bez podsumowania" view.
- [ ] Deleting an entry removes its file after confirmation.
- [ ] A broken history file does not break the list.
- [ ] Session and profile ids are validated before any file path is built.

## 11. Tests and evaluation

- Unit tests with `tmp_path` and `monkeypatch` for `SESSIONS_DIR`; endpoint tests through `TestClient`.
- Manual check of the screens in the browser.
- No prompt changes, so no `tutor-eval`.

## Changelog

| Date | Change |
|---|---|
| 2026-11-08 | Document created. |
| 2026-11-08 | Accepted; open questions resolved with the proposed answers. |
