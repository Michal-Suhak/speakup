# 05. OpenAI and structured output

## Client

- One client per process (singleton, e.g. `@lru_cache` on `get_client()`).
- Key only from env (`OPENAI_API_KEY` via `python-dotenv`), never in code or the repo. Missing key: fail fast with a clear error.
- Keep the model name and `base_url` in config, not in code. Models change quickly and config should absorb that.
- Instructor (`instructor.patch(client)` / `from_openai`) connects OpenAI with Pydantic: `response_model=MySchema`.
- Check the current API (model names, Structured Outputs / Responses API) in the current OpenAI docs, not from memory.

## Every answer has a schema

```python
class TutorResponse(BaseModel):
    thinking: str = Field(..., description="Internal reasoning. Not shown to the student.")
    ai_answer: str = Field(..., description="Final message to the student, in English.")
```

- **`thinking` always comes before the answer.** The model thinks by generating tokens: without "thinking out loud" it's dumber. You also get a free look at its reasoning (gray box).
- Field descriptions (`description`) are instructions for the model, not comments for the programmer.
- A JSON Schema with `required` and `enum` beats asking "return JSON". Repeated keys act as rails, so don't economise on the format.

## Schema-guided reasoning (SGR)

Field order forces the order of thinking:

| Pattern | How | Example in the tutor |
|---|---|---|
| **Cascade** | `facts → assessment → decision` | `detected_mistakes → severity → should_correct → ai_answer` |
| **Routing** | `Union[A, B, C]` + `Literal` discriminator | `next_action: Correct \| AskFollowUp \| MoveToNextPhase` |
| **Cycle** | list with `min_length` / `max_length` | `mistakes: list[MistakeLog] = Field(max_length=5)` |

Example for corrections:

```python
class TurnAnalysis(BaseModel):
    detected_mistakes: list[MistakeLog] = Field(max_length=5)
    blocks_understanding: bool
    should_correct_now: bool          # depends on GENTLE/STRICT policy
    natural_alternative: str | None   # "real life" version of the learner's sentence
    ai_answer: str
```

## Validation

- Pydantic is the bouncer: data that doesn't match the schema raises an exception, so you will know.
- `Annotated[..., AfterValidator(...)]` for domain rules (e.g. CEFR level in A1–C2, `mastery` in [0, 1]).
- `max_retries` in Instructor automatically sends the validation error back to the model.
- Rules that can't be written in code are guarded by `llm_validator` (a second model), but only where plain validation isn't enough.

## Parameters

- Extraction, evaluation and routing: low `temperature`.
- Roleplay and conversation: moderate, so the agent doesn't sound wooden.
- A cheaper model for simple tasks (compression, classification), a stronger one for critical ones (plan, evaluation). Decide based on the leaderboard, not gut feeling.
