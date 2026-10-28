# Post-MVP backlog

Ideas to consider after the MVP ([0001](specs/0001-mvp.md)) is done. Just a list: no order, no commitment, no design.

To work on an item: discuss it, create a spec with the `feature-spec` skill, and remove the item from this list in the same PR (the spec takes over).

The backlog changes only through PRs, like everything on `main`. New ideas can be collected and added together in one "Update backlog" PR.

## Product

- **Session history and progress in SQLite** – save finished sessions and show progress over time; introduce SQLite (one local file) here, as the first feature that needs a database, and decide whether profiles move there too.
- **Login and internet deployment**

## Teaching

- **Vocabulary list with spaced repetition** – collect useful words from summaries, review them later and bring them back into conversations.
- **Recurring mistakes across sessions** – detect mistakes the learner keeps making and practise them.
- **Self-correction first** – for an important mistake, give a hint and let the learner fix it before showing the correct form.
- **Roleplay scenes** – restaurant, hotel, airport, job interview.
- **Pronunciation assessment**

## Voice and speed

- **Fast conversation mode** – OpenAI Realtime API: low latency, interrupting the tutor.
- **Automatic end-of-utterance detection (VAD)** – instead of push-to-talk.
- **Streaming replies** – stream the tutor's text and audio so the first words arrive within a few seconds.

## Quality

- **Tutor quality contract** – binary MUST/SHOULD checks with IDs and good/bad examples in a Markdown file, checking both the conversation and the returned data.
- **LLM judge** – score saved conversations against the quality contract (reasoning before each verdict).
- **Conversation simulator** – learner personas (levels, typical mistakes, Polish or one-word answers, injection attempts) talk to the tutor automatically; run before every prompt, schema or model change.
- **Choosing models by our own results** – compare chat models on the simulator and the judge (score, latency, cost) instead of public rankings.
- **Another tutor model** – e.g. Claude as an option.
