# 07. Evaluation, security, costs

## Metrics instead of vibe checks

- Manual "I'll chat and see" doesn't scale. A small prompt change has a butterfly effect elsewhere in the dialogue.
- Public rankings (Arena, MMLU etc.) measure marketing and data contamination, not your problem. **Your leaderboard matters more than a public one.**
- Off-the-shelf frameworks (RAGAS, DeepEval) give abstract numbers ("Faithfulness 0.78") that don't tell you what to fix.

## Your own leaderboard

- **Binary checks instead of 1–10 scales.** Break "should be helpful" into yes/no questions:
  - `PT-001` Did the agent avoid giving a ready answer to the homework?
  - `PT-002` With `GENTLE`, did it correct only mistakes that block understanding?
  - `PT-003` Did it offer a natural ("real life") version of the learner's sentence?
  - `PT-004` Did it refer to a fact from episodic memory?
  - `PT-005` In `HOMEWORK_CHECK`, did it avoid starting a new topic?
  - `PT-006` Did the profile get the correct level or goal? (state check, not only conversation)
- **Two sources of truth**: the conversation (`conversation_history`) **and** the state (`profile`, `workflow`). A nice conversation with a wrong JSON in the database is a failure.
- **Hierarchy**: check → category → priority (MUST / SHOULD / NICE) → score (e.g. Silver / Gold / Diamond).
- **Leaderboard card as Markdown in git**, with positive and negative examples (few-shot for the judge). Parse it with regex (deterministic) and generate the verdict schema with `create_model`.

## LLM-as-judge

```python
class Verdict(BaseModel):
    reasoning: str      # reasoning first...
    is_correct: bool    # ...then the verdict
```

- Field order matters: `reasoning` first, then the verdict (critique shadowing).
- Split checks into areas (namespaces) rather than one call for everything. A cheaper judge for simple checks, a more expensive one for critical ones.

## Conversation simulator

- A second LLM plays the learner using a **persona** (level, typical mistakes, goal, mood: stressed Marek B1, perfectionist C1 with `STRICT`, someone who answers in one word).
- Run whole sessions automatically, then pass them through the judge. No more typing "Hi" by hand for the thousandth time.
- Edge-case scenarios as an enum (shadow system): learner writes in Polish, stays silent, asks for a ready answer, attempts prompt injection.
- On every prompt, schema or model change: run the leaderboard and compare.

## Security and privacy

- **Secrets** only in env or a secret manager. `.env` in `.gitignore`.
- **Prompt injection**: learner text and transcripts are data, not instructions. Keep them in separate tags and put core rules above them. Never store "facts" in memory that are actually commands.
- **Memory poisoning**: validate what goes into the profile. The model may hallucinate a fact that then stays in memory forever.
- **Pseudonymisation**: personal data (names, addresses, companies from the learner's stories) can be masked locally (e.g. spaCy on CPU) before sending to the cloud and unmasked in the answer. A hybrid architecture beats running your own local model.
- **Voice recordings** are sensitive data (biometrics). Store them only when needed, with a retention policy and user consent.

## Costs and safeguards

- Hard limits: agent loop iterations, `max_tokens`, number of retries, number of episodes in context.
- Log token usage and TTS characters per session and per learner.
- Episode compression and context selection are the main cost levers (90–99% fewer tokens than raw history).
- Do heavy processing (compression, analytics) async after the session, not on the hot path of the conversation.
