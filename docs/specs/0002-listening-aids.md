# 0002 – Listening aids: reply translation, slower repeat, English-only transcription

| Field | Value |
|---|---|
| Status | `in-progress` |
| Created | 2026-10-29 |
| Last updated | 2026-10-29 |
| Depends on | [0001](0001-mvp.md) |
| Supersedes | – |

## 1. Problem and context

Learners at A1–B1 often do not understand the tutor's reply. They can only replay it at the same speed, and then the conversation stalls. Learners with a strong Polish accent have a different problem: the transcription sometimes comes out as Polish-looking phonetics, so the tutor answers something they never said. All three fixes are small and touch the same voice loop, so they go in one spec, delivered in three stages.

## 2. Goal

The learner can read a Polish translation of any tutor reply, hear it again more slowly, and make the app always transcribe their speech as English.

## 3. Scope

**In scope:**
- `reply_pl` in the tutor's structured answer (also for the greeting), shown under each tutor line on click, unfolded by default for A1–A2.
- A "wolniej" button that replays the last reply at 0.75× speed in the browser.
- A profile field `speech_language` (`auto` or `en`), passed to the transcription as `language="en"` when set to `en`.

**Out of scope:**
- Translating the learner's own messages or the summary (the summary is already in Polish where it matters).
- Speaking the translation, or a Polish voice.
- A second TTS call at a slower speed, or a speed setting in the profile.
- Other transcription languages than English.

## 4. User scenarios

1. **Translation, A2 learner:** the tutor says "Did you go anywhere nice last weekend?". Under the line the translation is already unfolded: „Czy w zeszły weekend udało ci się gdzieś wyjechać?” (gender-neutral, no „pojechałeś”). "ukryj tłumaczenie" folds it.
2. **Translation, B2 learner:** the same line shows only the "przetłumacz" link. A click unfolds the translation, a second click folds it again.
3. **Translation missing or broken:** the model returns an empty `reply_pl`. The line shows no link; the conversation goes on.
4. **Slower repeat:** after the reply has played, the learner clicks "wolniej". The same audio plays at 0.75× with normal pitch. "powtórz" plays it at normal speed again. Both buttons are disabled while the tutor is speaking or thinking and hidden when there is no audio.
5. **English-only transcription:** in the profile the learner sets "Rozpoznawanie mowy" to "zawsze po angielsku". The learner says "I go to the shop yesterday" with a strong accent; the transcript is English words, with the grammar mistake kept.
6. **English-only and a Polish word:** with `en`, the learner says a Polish word ("I like pierogi"). The transcript may spell it in an English way or drop it. This is the trade-off of `en`, so `auto` stays the default and the option's label says so.
7. **Old profile file** without `speech_language`: it loads as `auto`, behaviour does not change.

## 5. Solution design

### Architecture and flow

- `tutor/schemas.py` – `TutorTurn.reply_pl` after `reply`, so the model translates the reply it has just written.
- `api/sessions.py` – `reply_pl` in `StartResponse` and `TurnResponse` (and so `VoiceTurnResponse`).
- `tutor/session.py` – unchanged: only `reply` goes into the history, the translation is never sent back to the model.
- `tutor/profiles.py` – `speech_language` field.
- `tutor/stt.py` – `transcribe` gets the language; `language="en"` is passed only for `en`, nothing for `auto` (same call as today).
- `static/app.js`, `static/index.html`, `static/style.css` – translation toggle, "wolniej" button, profile select.

### Data and formats

Turn answer (model output and `/api/text`, `/api/turn` response), new field `reply_pl`:

```json
{
  "reply": "Oh, you went to Spain last summer? Nice! What did you like most there?",
  "reply_pl": "O, zeszłego lata Hiszpania? Super! Co ci się tam najbardziej podobało?",
  "corrections": [
    {
      "you_said": "Last summer I go to Spain",
      "better": "Last summer I went to Spain",
      "explanation_pl": "Mówimy o przeszłości, więc używamy formy „went”."
    }
  ],
  "audio": "<base64 mp3>"
}
```

`POST /api/session` response: `{"session_id": "…", "reply": "…", "reply_pl": "…", "audio": "…"}`.

Profile, new field (default `auto`):

```json
{
  "id": "michal",
  "name": "Michał",
  "level": "B1",
  "interests": ["Travel", "Work"],
  "goals": "Speak in meetings at work",
  "avoid_topics": [],
  "correction_style": "gentle",
  "speech_language": "en"
}
```

### Endpoints

| Method | Path | Input → output |
|---|---|---|
| POST | `/api/session` | unchanged input → adds `reply_pl` |
| POST | `/api/text` | unchanged input → adds `reply_pl` |
| POST | `/api/turn` | unchanged input → adds `reply_pl` |
| GET/PUT | `/api/profiles/{id}` | adds `speech_language` (`auto` \| `en`) |

`reply_pl` is a string; an empty string means no translation.

### Prompts

- `TutorTurn.reply_pl` field description: a natural Polish translation of `reply`, same meaning and tone, plain text; addresses the learner without assuming gender (as in `prompts/summary.md`); empty string if unsure.
- `prompts/tutor.md`: the field order line becomes `analysis`, `corrections`, `reply`, `reply_pl`. The rule "speak only English" stays: it applies to `reply`.
- `prompts/transcribe.md` unchanged.

### Interface

- Under each tutor line: link "przetłumacz" / "ukryj tłumaczenie" and the Polish text in the muted explanation style. Unfolded by default when the profile level is A1 or A2.
- Next to "powtórz": button "wolniej" (`playbackRate = 0.75`, `preservesPitch` left on). "powtórz" sets the rate back to 1.
- Profile form: "Rozpoznawanie mowy" with options "automatycznie (rozpoznaje też polskie słowa)" and "zawsze po angielsku (przy mocnym akcencie)".
- All new strings used from JS go into `TEXT` in `static/app.js`.

## 6. Decisions

| Decision | Choice | Alternatives | Why |
|---|---|---|---|
| Where the translation comes from | `reply_pl` field in the same structured answer | A separate translation call on click | No extra call or wait on click; the model translates its own sentence, so meaning matches. |
| Translation for every level | Always generated, shown by default only for A1–A2 | Two schemas, translation only for low levels | One schema and one code path; the extra output tokens cost little (section 7). |
| Translation in the history | Not stored in `session.messages` | Store the whole turn | The model should see only English replies; it keeps the context short. |
| Slower repeat | Browser `playbackRate` 0.75 on the audio already downloaded | Second TTS call with slower instructions | Instant, free, no new endpoint. Pitch is preserved by default in current browsers. |
| Transcription language | Profile field `auto` \| `en`, default `auto` | Always `en`; per-session switch | `en` drops Polish words, which the tutor uses to suggest the English word (`polish_word` corrections), so it is opt-in per learner. |
| One spec for three changes | One spec, three stages, one PR per stage | Three specs | Each change is a few dozen lines on the same voice loop. |

## 7. Cost, latency, privacy

- **OpenAI calls:** no new calls. The tutor answer gets ~30–60 more output tokens per turn (≈0.00003 USD at the rates in `config.py`), counted in the existing usage.
- **Latency:** the reply is generated before `reply_pl`, but TTS starts only after the whole answer, so each turn waits for the translation too: expected +0.3–0.6 s. Measured in stage 3 with the existing "LLM took N s" log; if it is over 1 s, we generate it only for A1–B1 (see section 8).
- **Slower repeat** and **transcription language** add no cost; `language="en"` may make transcription slightly faster.
- **Privacy:** no new stored data apart from one profile field. Logs stay as they are (no translation text, no transcripts).

## 8. Risks and open questions

- [x] Extra latency of `reply_pl` for B2–C2: accepted as is. If stage 3 measures more than 1 s extra, the translation is generated only for A1–B1.
- [x] Slower speed: 0.75×; changed to 0.8× only if it sounds unnatural in the stage 2 check.
- [x] `language="en"` and the learner's grammar mistakes: assumed kept, since the transcription prompt asks for that; checked with a few recordings in stage 1.
- Risk: the model sometimes returns an English or partial `reply_pl`. Low impact: it is only shown on click and the description allows an empty string.

## 9. Implementation plan

**Stage 1 – transcription language**
- [x] `speech_language` in `Profile`, default `auto`.
- [x] `transcribe` passes `language="en"` for `en`; callers pass the session profile's value.
- [x] Profile form select; README line about the option.
- [x] Tests: profile default and validation, `transcribe` passes `language` only for `en`.

**Stage 2 – slower repeat**
- [x] "wolniej" button, rate reset in "powtórz" and for every new reply, disabled and hidden with "powtórz".
- [ ] Manual check in Chrome and Safari.

**Stage 3 – reply translation**
- [ ] `reply_pl` in `TutorTurn`, prompt field order line.
- [ ] `reply_pl` in the start and turn responses.
- [ ] Translation toggle under tutor lines, unfolded for A1–A2.
- [ ] Tests: responses contain `reply_pl`, history contains only `reply`.
- [ ] Manual check of a few turns at A2 and B2 (meaning, gender-neutral form, latency in the log).

## 10. Acceptance criteria

- [x] A profile without `speech_language` loads as `auto`; `auto` sends the same transcription request as before.
- [x] With `en` the transcription request has `language="en"`.
- [x] "wolniej" replays the last reply at 0.75× without an API call; "powtórz" plays it at 1×; a new reply plays at 1×.
- [x] Both replay buttons are disabled while the tutor is thinking or speaking and hidden when there is no audio.
- [ ] Every tutor line with a non-empty `reply_pl`, including the greeting, has a working "przetłumacz" toggle; lines with an empty one have no toggle.
- [ ] For A1–A2 the translation is unfolded by default, for B1–C2 folded.
- [ ] `reply_pl` is never spoken and never sent back to the model.
- [ ] Translations in the manual check do not assume the learner's gender.

## 11. Tests and evaluation

- Unit tests (pytest, `TestClient`, fake OpenAI client as in `tests/conftest.py`): profile field, `transcribe` arguments, `reply_pl` in responses, history content.
- Manual: recordings with a strong accent in `auto` and `en`; slower repeat by ear in Chrome and Safari; a few A2 and B2 turns for translation quality and latency.
- `tutor-eval`: the tutor prompt changes only in the field order line, so a short manual check is enough; no eval batch.

## Changelog

| Date | Change |
|---|---|
| 2026-10-29 | Document created. |
| 2026-10-29 | Accepted; open questions resolved with the default answers, each checked in its stage. |
| 2026-10-29 | Stage 1 implemented: `speech_language` in the profile and the profile form, `language="en"` passed to transcription. |
| 2026-10-29 | Stage 2 implemented: "wolniej" replays the last reply at 0.75× in the browser. |
