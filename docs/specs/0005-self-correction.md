# 0005 – Self-correction first

| Field | Value |
|---|---|
| Status | `accepted` |
| Created | 2026-11-08 |
| Last updated | 2026-11-08 |
| Depends on | [0001](0001-mvp.md), [0003](0003-practice-modes.md) (hint pattern) |
| Supersedes | – |

## 1. Problem and context

Today the tutor fixes an important mistake straight away: it recasts the correct form in its reply and the correction appears on screen. The learner reads the answer but does not have to produce it. Finding and fixing one's own mistake is a stronger learning step ([04-pedagogy](../guidelines/04-pedagogy-and-session.md): "Socratic, it doesn't hand out answers, it guides"). It also slows the conversation down, so it must be optional.

## 2. Goal

A learner who turns the option on gets one chance to fix an important mistake after a hint, before the tutor shows the correct form.

## 3. Scope

**In scope:**
- A profile option "Daj mi szansę się poprawić", off by default.
- For one important mistake per turn: a short English hint instead of the normal reply, one retry, then praise or the correct form.
- Works for voice and text turns.

**Out of scope:**
- Hints for minor mistakes, or for more than one mistake per turn.
- More than one retry.
- Counting self-corrections in the summary or history (possible later on 0004 data).

## 4. User scenarios

1. **Fixed:** option on. The learner says "Last summer I go to Spain". Instead of the usual reply the tutor says "Almost! Can you say that again, but about last summer?". Under the learner's line: "spróbuj się poprawić". The learner says "Last summer I went to Spain". The tutor says "Yes, perfect! So what did you see there?". Under the first line: "✓ poprawione samodzielnie".
2. **Not fixed:** the retry is "Last summer I goed to Spain". The tutor gives the correct form naturally ("Nearly! We say: I went to Spain. What did you see?") and the usual correction appears under the first line.
3. **Retry with another mistake:** the retry fixes the first mistake but has a new important one. The new one gets a normal correction, never a second hint (no hint chains).
4. **Off-topic, Polish or silence on retry:** an empty or too-short recording behaves as today (error message, retry still pending). Any real answer that does not fix the mistake counts as "not fixed" (scenario 2).
5. **Several mistakes:** the hint is about the first important one; the others are shown as normal corrections right away.
6. **Option off or only minor mistakes:** behaviour as today.
7. **Session ends during a retry:** "zakończ sesję" works normally; the pending mistake is in the conversation, so the summary can still mention it.

## 5. Solution design

### Architecture and flow

Python decides the flow; the model only writes the hint and judges the retry ([01-architecture](../guidelines/01-architecture.md): LLM decides content, Python decides flow).

1. Learner turn, no retry pending, option on, at least one important visible correction → Python takes the first important one as `pending_retry` on the session, sends the model's `hint` as the spoken reply, and keeps the other corrections visible. The history stores the learner message and the hint, so the model sees the context.
2. Next learner turn with `pending_retry` → the system prompt gets a "Retry" section with the mistake and the expected form; the model fills `retry_fixed` and writes a `reply` that starts with praise or with the correct form. Python clears `pending_retry` whatever the result, and returns the pending correction for display when not fixed.
3. A turn never sets a new `pending_retry` while one is being resolved (no chains).

Changes:
- `tutor/profiles.py` – `self_correction: bool = False`.
- `tutor/schemas.py` – `TutorTurn.hint` and `TutorTurn.retry_fixed`.
- `tutor/session.py` – `pending_retry: Correction | None`.
- `tutor/llm.py` – the flow above in `reply()`, the retry section in `render_system_prompt`.
- `api/sessions.py` – new response fields.
- `static/` – profile option with hint, "spróbuj się poprawić" note, result on the original line.

### Data and formats

Model answer (new fields, after `reply_pl`):

```json
{
  "analysis": "Past time, 'go' should be 'went'.",
  "corrections": [{"you_said": "Last summer I go", "better": "Last summer I went", "mistake_type": "grammar", "severity": "important", "explanation_pl": "Mówimy o przeszłości, więc «went»."}],
  "reply": "Oh, you went to Spain last summer? Nice! What did you see?",
  "reply_pl": "O, zeszłego lata Hiszpania? Super! Co udało ci się zobaczyć?",
  "hint": "Almost! Can you say that again, but about last summer?",
  "retry_fixed": false
}
```

- `hint`: one short English sentence that points at the rule without giving the correct form; empty when there is no important mistake.
- `retry_fixed`: meaningful only when the prompt has a Retry section; otherwise false.

Turn response, new fields:

```json
{
  "reply": "Almost! Can you say that again, but about last summer?",
  "reply_pl": "Prawie! Możesz powiedzieć to jeszcze raz, ale o zeszłym lecie?",
  "corrections": [],
  "retry": "waiting",
  "revealed": [],
  "audio": "<base64 mp3>"
}
```

- `retry`: `"waiting"` (the reply is a hint), `"fixed"`, `"not_fixed"` or `null` (no retry involved).
- `revealed`: the pending correction when `not_fixed`, shown under the original learner line; otherwise empty.
- When `retry` is `"waiting"`, `reply_pl` translates the hint, and the hint is what TTS speaks.

Profile, new field (default `false`): `"self_correction": true`.

### Prompts

- `TutorTurn.hint` description: hint without the answer, name the area ("about the past", "one person"), at most 15 words, encouraging.
- `prompts/tutor.md`, section filled only during a retry:
  ```
  # Retry
  The learner is trying to fix this mistake: "$you_said" → "$better".
  Set retry_fixed to true if their message now uses the correct form. Start the reply with short praise if fixed;
  otherwise say the correct form naturally once. Then continue the conversation.
  ```
  Otherwise the section renders "none". `$you_said` and `$better` are model output from the previous turn, kept inside quotes as data.

### Interface

- Profile form: "Daj mi szansę się poprawić" (tak / nie) with (i): „Gdy zrobisz ważny błąd, tutor najpierw podpowie, a ty spróbujesz powiedzieć to jeszcze raz. Dopiero potem zobaczysz poprawną wersję.”
- Under the learner line during a retry: "spróbuj się poprawić" in the pen colour.
- After the retry, under the same line: "✓ poprawione samodzielnie" or the usual correction card.
- New JS strings in `TEXT`.

## 6. Decisions

| Decision | Choice | Alternatives | Why |
|---|---|---|---|
| Who decides when to hint | Python, from the visible important corrections | The model decides in its reply | Flow is code; the decision is testable and respects `correction_style`. |
| Who judges the retry | The model (`retry_fixed`) | String match of `better` in the retry | Learners fix mistakes with different words ("I went", "I travelled"); a string match would fail them. |
| Extra calls | None: `hint` comes with every answer | A second call to write the hint | No added latency; the unused hint costs ~20 output tokens. |
| Default | Off | On | Changes the feel of the conversation; existing learners keep today's behaviour. |
| Retries | One, no chains | Until fixed | Avoids frustration and loops; the conversation keeps moving. |

## 7. Cost, latency, privacy

- **OpenAI calls:** none added. ~20 more output tokens per turn for `hint`, plus one extra learner turn per important mistake when the option is on.
- **Latency:** no change per turn.
- **Privacy:** no new stored data apart from one profile field; `pending_retry` lives in memory with the session.

## 8. Risks and open questions

- [x] Hint giving away the answer: guarded by the field description; checked on ~10 hand-written mistakes in stage 2, adding bad/good hint examples if needed.
- [x] Fair `retry_fixed` judgement when the learner rephrases: same check in stage 2.
- Risk: learners with "gentle" correction have fewer important mistakes, so the option rarely triggers. Acceptable: it follows the same rule as visible corrections.

## 9. Implementation plan

**Stage 1 – data and flow**
- [ ] `self_correction` in the profile and form, with hint.
- [ ] `hint`, `retry_fixed`, `pending_retry`, Retry section, response fields.
- [ ] Tests: hint chosen only for important mistakes with the option on; one retry; fixed / not fixed responses; no chain; option off unchanged.

**Stage 2 – interface and check**
- [ ] "spróbuj się poprawić" note and result on the original line.
- [ ] Manual check on ~10 mistakes by text and voice (hint does not reveal the answer, retry judged fairly).

## 10. Acceptance criteria

- [ ] With the option off, turns behave and return as before (new fields `retry: null`, `revealed: []`).
- [ ] With the option on and an important mistake, the spoken reply is the hint and the correction is not shown yet.
- [ ] The next turn resolves the retry: praise and "✓ poprawione samodzielnie", or the correct form and the correction under the original line.
- [ ] A turn that resolves a retry never starts a new one.
- [ ] Minor mistakes never trigger a hint.

## 11. Tests and evaluation

- Unit tests with a fake `_ask` for the flow and the response fields; endpoint tests through `TestClient`.
- Manual check on ~10 mistakes (about 20 chat calls, under 0.01 USD).
- `tutor-eval`: the prompt gets a new section and two fields → manual check as above; candidates for the future quality contract: "hint does not contain the correct form", "retry judged correctly".

## Changelog

| Date | Change |
|---|---|
| 2026-11-08 | Document created. |
| 2026-11-08 | Accepted; open questions resolved with the proposed answers. |
