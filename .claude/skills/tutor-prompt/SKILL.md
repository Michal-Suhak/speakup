---
name: tutor-prompt
description: Write or change the tutor's prompts in prompts/ (tutor.md, summary.md) and how they are rendered. Use when changing tutor behaviour, correction style, level adaptation, topics or the session summary.
---

# Tutor prompt

Background: [docs/guidelines/02-context-and-prompts.md](../../../docs/guidelines/02-context-and-prompts.md), [docs/guidelines/04-pedagogy-and-session.md](../../../docs/guidelines/04-pedagogy-and-session.md).

## Steps

1. Read the current prompt file and the code that renders it.
2. Decide the change in terms of behaviour first ("tutor should recast mistakes instead of explaining them"), then edit the prompt.
3. Keep the structure:
   - role and identity (friendly English tutor, not an OpenAI model),
   - hard rules (English only, 2–4 sentences, end with a question, TTS-friendly text: no markdown, emoji, lists, brackets),
   - correction policy (recast clear mistakes naturally, ignore small slips and likely transcription errors),
   - current settings (`{topic}`, `{level}`, optional voice/speed),
   - processing priority if there are several sections.
4. Instructions in English. Use clear section headers or XML-like tags; keep it short, every line must earn its place.
5. Render the prompt with sample data and read the final text before calling the API.
6. Check with 3–5 sample turns: a correct answer, a clear grammar mistake, a one-word answer, an answer in Polish, an off-topic answer.

## Turn output

- Every tutor turn returns `{reply, corrections[]}` as defined in `docs/specs/0001-mvp.md`. `reply` is spoken English for TTS; each correction has `you_said`, `better`, `explanation_pl`. `corrections` may be empty.
- Every `you_said` must quote what the learner actually said in this turn.

## Summary prompt

- Output must match the summary schema in `docs/specs/0001-mvp.md` (`top_corrections`, `useful_vocabulary`, `strengths`, `tip_pl`; max 3 corrections and 3 words).
- Use a Pydantic model + structured output; field order: evidence first, scores last.
- Explanations in Polish, examples in English.

## Do not

- Do not put prompt text into Python code.
- Do not add rules that conflict with existing ones; replace instead of stacking.
- Do not grow the prompt to fix one edge case without checking it does not break the others.
