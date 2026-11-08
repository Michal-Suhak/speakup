# 0003 – Practice modes and plain-language help: tooltips, session cleanup, listening mode, scenes, "Jak powiedzieć…?"

| Field | Value |
|---|---|
| Status | `in-progress` |
| Created | 2026-11-08 |
| Last updated | 2026-11-08 |
| Depends on | [0001](0001-mvp.md), [0002](0002-listening-aids.md) |
| Supersedes | – |

## 1. Problem and context

SpeakUp is now used by learners who are not technical (e.g. a younger sibling on Windows). Several controls are not obvious without explanation: "nowa rozmowa" and "zakończ sesję" look alike, "Poziom" uses CEFR codes, "Rozpoznawanie mowy" needs context. At the same time the conversation offers only free topics: there is no way to practise everyday situations, to train listening without reading, or to ask how to say a word. On the server, sessions that are never ended stay in memory until a restart and their cost is never logged.

## 2. Goal

A learner who has never seen the app understands every control from short Polish hints, can practise everyday scenes, listening and asking for words, and abandoned sessions no longer pile up.

## 3. Scope

**In scope:**
- An (i) hint pattern with tooltips, used on every control whose label is not self-explanatory (existing and new ones).
- Ending sessions after 30 minutes without activity, with their cost logged.
- A listening mode switch that hides the tutor's text until clicked.
- Scenes: roleplay situations on the start screen, with the tutor playing a role.
- "Jak powiedzieć…?": asking in Polish how to say something, answered inside the normal turn.

**Out of scope:**
- An onboarding tour or tutorial screens.
- Custom scenes written by the learner (the custom topic field covers free practice).
- A separate dictionary call or a dictionary screen.
- Saving finished or expired sessions (that is [0004](0004-session-history.md)).

## 4. User scenarios

1. **First visit:** the learner sees "Poziom" with an (i) next to it. Hovering (mouse) or tapping (phone, tablet) shows: "Twój poziom angielskiego, od A1 (początkujący) do C2 (biegły)…". Tapping anywhere else or pressing Esc closes it. With the keyboard, Tab reaches the (i) and the hint shows on focus.
2. **Ending a conversation:** the learner is unsure whether to click "nowa rozmowa" or "zakończ sesję". The (i) next to them explains that only "zakończ sesję" gives a summary.
3. **Abandoned session:** the learner closes the laptop lid mid-conversation and comes back after an hour. The next message shows "Ta rozmowa wygasła po dłuższej przerwie. Kliknij „nowa rozmowa”." The server log has one line "Session … expired: … USD".
4. **Listening mode:** the learner switches on "ukryj tekst tutora". New tutor lines show only "pokaż tekst" while the voice plays. A click reveals that line (with its translation toggle). The learner's own lines and corrections stay visible. Switching the mode off reveals all lines.
5. **Scene:** on the start screen the learner picks "W restauracji". The tutor greets as a waiter ("Good evening! Do you have a reservation?"), stays in role, still corrects mistakes as set in the profile. "zakończ sesję" gives the usual summary.
6. **"Jak powiedzieć…?" by text:** mid-conversation the learner types "jak powiedzieć rachunek?". The tutor answers "It's "the bill". You can say: Could we have the bill, please?" and continues the topic. The question is not marked as a mistake.
7. **"Jak powiedzieć…?" by voice with English-only transcription:** with "zawsze po angielsku" the Polish question is transcribed badly. The hint next to the text field says to type such questions.
8. **Busy tutor:** while the tutor is thinking, the (i) hints still open; they never block the mic or buttons.

## 5. Solution design

### Architecture and flow

- `static/index.html`, `static/style.css`, `static/app.js` – hint markup and behaviour, listening switch, scene buttons, new texts.
- `tutor/session.py` – `last_active` on `Session`, refreshed by `turn()`; `expire_idle_sessions()` removes sessions idle for more than `SESSION_IDLE_MINUTES = 30` and not busy, logging id, idle minutes and cost; called from `register_session` and `get_session`, so no background thread is needed.
- `api/sessions.py` – `StartRequest.scene` (optional); the start endpoint checks it against the known scenes.
- `prompts/scenes/<id>.md` – one file per scene with the role and situation in English.
- `prompts/tutor.md` – a `$scene` section and a "Jak powiedzieć" rule.
- `tutor/llm.py` – renders the scene text (or "none") into the system prompt.

### Hint pattern (tooltips)

Markup, next to the control (never inside a button or label text, so the control keeps its own click):

```html
<span class="hint">
  <button type="button" class="info" aria-label="Co to jest?" aria-expanded="false" aria-describedby="tip-level">i</button>
  <span class="tip" role="tooltip" id="tip-level">Twój poziom angielskiego…</span>
</span>
```

- Shown on mouse hover and on keyboard focus (CSS `:hover`, `:focus-visible`).
- Tap or click toggles it (`aria-expanded`), because touch devices have no hover and Safari does not focus buttons on click; a click outside or Esc closes it. One small delegated handler in `app.js`.
- Only one hint open at a time.
- The (i) is a round 24×24 px target (minimum touch size), in the pencil colour so it does not compete with actions.
- The tooltip: max-width `min(280px, 90vw)`, stays inside the screen on phones, short plain Polish (1–2 sentences, no jargon such as STT, CEFR without explanation, API, sesja w sensie technicznym).
- Hint texts are markup text, so they live in `index.html`; the scene list too.

Hints and their texts:

| Where | Text |
|---|---|
| Poziom | „Twój poziom angielskiego, od A1 (początkujący) do C2 (biegły). Tutor dopasuje do niego słówka i długość zdań. Nie wiesz? Wybierz B1.” |
| Lubię rozmawiać o | „Te tematy pojawią się jako przyciski, gdy będziesz zaczynać rozmowę.” |
| Mój cel | „Po co uczysz się angielskiego, np. «rozmowy w pracy». Tutor będzie do tego nawiązywać.” |
| Omijamy tematy | „Tematy, o które tutor nigdy nie zapyta.” |
| Poprawiaj mnie | „Łagodnie: tutor poprawia tylko ważne błędy. Dokładnie: poprawia każdy błąd.” |
| Rozpoznawanie mowy | „Zostaw «automatycznie». «Zawsze po angielsku» pomaga, gdy aplikacja zapisuje twoje angielskie zdania jak polskie słowa.” |
| Tematy (start) | „Wybierz temat i po prostu rozmawiaj. Możesz też wpisać własny.” |
| Scenki (start) | „Tutor gra rolę, np. kelnera, a ty ćwiczysz prawdziwą sytuację.” |
| Mikrofon | „Przytrzymaj przycisk (albo spację), powiedz zdanie po angielsku i puść. Tutor odpowie głosem.” |
| powtórz / wolniej | „«powtórz» odtwarza ostatnią odpowiedź tutora jeszcze raz, «wolniej» – w wolniejszym tempie.” |
| Pole tekstowe | „Możesz też pisać. Nie wiesz, jak coś powiedzieć? Napisz po polsku, np. «jak powiedzieć rachunek?».” |
| ukryj tekst tutora | „Ćwiczysz słuchanie: tekst tutora jest ukryty, dopóki nie klikniesz «pokaż tekst».” |
| Rozmowa (nagłówek) | „Pod twoim zdaniem pojawi się «poprawki», jeśli tutor znalazł błąd. Pod odpowiedzią tutora «przetłumacz» pokazuje ją po polsku.” |
| nowa rozmowa / zakończ sesję | „«zakończ sesję» kończy rozmowę i pokazuje podsumowanie: błędy, słówka i wskazówkę. «nowa rozmowa» wraca do wyboru tematu bez podsumowania.” |
| Koszt (podsumowanie) | „Przybliżony koszt tej rozmowy w usłudze OpenAI, z której korzysta tutor.” |

### Scenes

| Id | Button (Polish) | Tutor's role |
|---|---|---|
| `restaurant` | W restauracji | waiter in a casual restaurant |
| `hotel` | W hotelu | hotel receptionist at check-in |
| `airport` | Na lotnisku | check-in agent at the airport |
| `job-interview` | Rozmowa o pracę | friendly interviewer for a job the learner chooses |
| `doctor` | U lekarza | GP asking about symptoms |
| `shop` | W sklepie | shop assistant in a clothes shop |

Start request with a scene; `topic` carries the scene's English title, so history and the summary need no change:

```json
{"profile_id": "michal", "topic": "At a restaurant", "scene": "restaurant"}
```

An unknown `scene` returns 422. Without `scene` the session works as today.

### Prompts

- `prompts/tutor.md`, new section:
  ```
  # Scene
  $scene
  ```
  With a scene: "Play this role: … Stay in the role, keep the situation realistic, and still follow the correction rules." Without: "none – a free conversation on the session topic."
- `prompts/scenes/*.md`: role, setting and what the learner should practise (e.g. ordering, asking for the bill), 3–5 lines each.
- New rule in "Rules": when the learner asks in Polish how to say something ("jak powiedzieć…", "jak jest po angielsku…"), give the natural English word or phrase with one short example sentence and go back to the topic; such a question is not a mistake and gets no correction.
- The scene and the question are data from a closed list or from the learner; the learner's text stays in the message, never in the instructions.

### Interface

- Start screen: a "Scenki" row of buttons under the topics.
- Chat: a checkbox switch "ukryj tekst tutora" next to "powtórz" / "wolniej"; hidden lines show a "pokaż tekst" link.
- Expired session message: „Ta rozmowa wygasła po dłuższej przerwie. Kliknij „nowa rozmowa”.” (replaces the current restart-only text, which is still true after a restart).
- All new JS strings go into `TEXT` in `static/app.js`.

## 6. Decisions

| Decision | Choice | Alternatives | Why |
|---|---|---|---|
| Tooltip mechanism | Own (i) button + CSS, tap toggles, small JS for click and Esc | `title` attribute; a tooltip library | `title` does not work on touch, shows late and is not read reliably by screen readers; a library adds a dependency and a build step. |
| Where hints go | Only on controls whose label is not self-explanatory | (i) on every control | Too many icons are noise; a clear label needs no hint. |
| Session cleanup trigger | Check idle sessions on every register and lookup | Background timer thread | No extra thread or scheduler; with one user the check is free. |
| Idle limit | 30 minutes, constant in `session.py` | Setting in `.env` | A value that never changes does not need config. |
| Scenes source | Fixed list, prompt per scene in `prompts/scenes/` | Free-text scenes; LLM-generated scenes | Predictable roles and testable prompts; the custom topic already covers free practice. |
| "Jak powiedzieć…?" | Prompt rule inside the normal turn | Separate button and API call | No extra cost, no new endpoint; works by text and by voice. |
| Listening mode state | Switch kept until the page is reloaded | Profile field | A practice choice per sitting, not a learner setting; keeps the profile format unchanged. |

## 7. Cost, latency, privacy

- **OpenAI calls:** none added. The scene section and the new rule add ~100–200 input tokens per turn (≈0.00002 USD).
- **Latency:** no change.
- **Privacy:** no new stored data. The expiry log line has only the session id, idle minutes and cost.

## 8. Risks and open questions

- [x] Corrections in scenes: expected to keep working, since the scene section repeats the correction rules; checked by hand on two scenes in stage 4.
- [x] "jak powiedzieć…" as a `polish_word` mistake: prevented by the prompt rule; checked in stage 5, and if it still happens the rule moves into the `corrections` field description too.
- Risk: tooltips cover the control below them on small phones. Mitigated by max width and placement above the (i) when there is no room below.

## 9. Implementation plan

**Stage 1 – hints**
- [x] Hint markup, styles and the click / Esc handler.
- [x] Hints on the existing controls from the table.
- [x] Manual check: mouse, keyboard (Tab, Esc), phone width in the browser.

**Stage 2 – session cleanup**
- [x] `last_active`, `expire_idle_sessions()`, log line.
- [x] New expired-session message.
- [x] Tests: idle session removed and logged, busy session kept, active session kept.

**Stage 3 – listening mode**
- [x] Switch, hidden lines with "pokaż tekst", hint.
- [x] Manual check with voice and with the translation toggle.

**Stage 4 – scenes**
- [ ] `prompts/scenes/*.md`, `$scene` section, `StartRequest.scene` with validation.
- [ ] Scene buttons and hint on the start screen.
- [ ] Tests: prompt renders the scene and "none", unknown scene is 422.
- [ ] Manual check of two scenes.

**Stage 5 – "Jak powiedzieć…?"**
- [ ] Prompt rule, text field hint.
- [ ] Manual check by text and voice.

## 10. Acceptance criteria

- [ ] Every control listed in the hint table has an (i) that opens on hover, tap and keyboard focus, closes on Esc and outside click, and fits a 360 px wide screen.
- [x] A session idle for more than 30 minutes is removed on the next request and one log line with its cost is written; a busy session is never removed.
- [x] The next message to an expired session shows the new expired message.
- [x] With listening mode on, new tutor lines are hidden until "pokaż tekst"; switching it off shows all lines.
- [ ] Each scene starts with the tutor in role; corrections still appear.
- [ ] An unknown scene id is rejected with 422.
- [ ] "jak powiedzieć X?" gets the English phrase with an example and no correction.

## 11. Tests and evaluation

- Unit tests: session expiry (with a fake clock via `monkeypatch`), scene validation, prompt rendering with and without a scene.
- Manual: hints on desktop and phone width, listening mode, two scenes, "jak powiedzieć" by text and voice.
- `tutor-eval`: prompt changes (scene section, new rule) → a short manual check of a few turns per change; no eval batch.

## Changelog

| Date | Change |
|---|---|
| 2026-11-08 | Document created. |
| 2026-11-08 | Accepted; open questions resolved with the proposed answers. |
| 2026-11-08 | Stage 1 implemented: (i) hints on the existing controls; profile form fields use a `.field` wrapper so the (i) sits outside the `<label>` (a button inside a label would become its labelled control); the text field hint has only its first sentence until stage 5. |
| 2026-11-08 | Stage 2 implemented: sessions idle for more than 30 minutes are removed on the next request and logged with their cost; new expired message. |
| 2026-11-08 | Stage 3 implemented: "ukryj tekst tutora" switch hides new tutor lines behind "pokaż tekst"; switching it off reveals all. |
