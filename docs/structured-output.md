# Structured output in SpeakUp

How the tutor's answers are defined as Pydantic models, and the rules every new model must follow. Background: [guidelines 05](guidelines/05-openai-structured-output.md). Code: `tutor/schemas.py`, used by `tutor/llm.py`.

## Rules for every model sent to the LLM

1. **Field order is the order of thinking (cascade).** Facts first, then assessment, then the decision or the text for the user. The model generates fields top to bottom, so a field can only build on the fields above it.
2. **`description` is an instruction to the model, not a comment for developers.** It says what to put in the field, the format, the limits and, where it helps, a short example. The class docstring describes the whole answer. Both are sent to OpenAI in the JSON schema.
3. **Closed choices use `Literal`**, with every value explained in the description. No free-text categories.
4. **Lists have a maximum length** (`MaxLen`), so the model cannot flood the answer. The limit is enforced by the schema and by Pydantic.
5. **The LLM labels, Python decides.** The model reports facts and judgements (e.g. a mistake's `severity`); deterministic code applies business rules (which corrections the learner sees). Rules that can be checked in code are checked in code.
6. **Validate and retry.** A parse that fails validation is retried once (`PARSE_ATTEMPTS`), then the request fails with a readable `LLMError`.
7. **Internal fields stay internal.** Working fields (`analysis`, `mistake_type`, `severity`) are not part of the HTTP response; `api/` maps the model to the public JSON from the spec.
8. **Descriptions are in English**; values meant for the learner can be in Polish when the field says so (`explanation_pl`).

## `TutorTurn`

The tutor's answer to one learner message (and the greeting at session start).

| # | Field | Type | Role in the cascade |
|---|---|---|---|
| 1 | `analysis` | `str` | Attention anchor: 1-2 sentences on what the learner meant and which mistakes the message has. Not shown to the learner. |
| 2 | `corrections` | `list[Correction]`, max 5 | Every real mistake from the learner's last message, important ones first; minor ones too. |
| 3 | `reply` | `str` | What the tutor says: 2-4 TTS-friendly sentences ending with a question, with the needed fixes woven in. |

## `Correction`

| # | Field | Type | Meaning |
|---|---|---|---|
| 1 | `you_said` | `str` | Exact fragment copied from the learner's message (2-8 words). |
| 2 | `better` | `str` | The same fragment, fixed, changing only what is wrong. |
| 3 | `mistake_type` | `grammar` / `word_choice` / `polish_word` / `word_order` | Kind of mistake. |
| 4 | `severity` | `important` / `minor` | Impact on understanding; drives what the learner sees. |
| 5 | `explanation_pl` | `str` | One Polish sentence (max 15 words) explaining the fix. |

## What Python does with the answer

`tutor/llm.py`:

- **Start of session:** corrections are dropped; only `reply` is stored and returned.
- **Text turn:** a correction is shown only when
  - its `you_said` appears in the learner's message (case-insensitive), and
  - the profile's `correction_style` is `strict`, or the correction's `severity` is `important`;
  - important corrections come first and at most 3 are shown.
- The reply is stored in the session history; `analysis` is discarded.

Public response of `POST /api/text` (unchanged from the spec):

```json
{
  "reply": "Oh, you went to Spain last summer? Nice! What did you enjoy most?",
  "corrections": [
    {"you_said": "Last summer I go to Spain", "better": "Last summer I went to Spain", "explanation_pl": "Mówimy o przeszłości, więc używamy formy „went”."}
  ]
}
```

## Adding a new model

- Put it in `tutor/schemas.py` and follow the rules above.
- `tests/test_schemas.py` checks that every field has a meaningful description, the field order, and the limits in the generated schema; extend it for the new model.
- Record the public JSON shape in the spec before exposing it through the API.
