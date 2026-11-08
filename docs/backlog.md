# Post-MVP backlog

Ideas to consider after the MVP ([0001](specs/0001-mvp.md)) is done. Just a list: no order, no commitment, no design.

To work on an item: discuss it, create a spec with the `feature-spec` skill, and remove the item from this list in the same PR (the spec takes over).

The backlog changes only through PRs, like everything on `main`. New ideas can be collected and added together in one "Update backlog" PR.

## Product

- **Progress screen** – practice time, sessions per week and common mistakes, built on the saved sessions from [0004](specs/0004-session-history.md).
- **Admin panel in the browser** – accounts, limits and usage without the terminal commands from the online deployment draft, for when there are more learners.
- **Memory for long conversations** – summarise older turns instead of cutting the history at the last 40 messages.

## Teaching

- **Vocabulary list with spaced repetition** – collect useful words from summaries, review them later and bring them back into conversations.
- **Recurring mistakes across sessions** – detect mistakes the learner keeps making and practise them.
- **Pronunciation assessment**

## Voice and speed

- **Fast conversation mode** – OpenAI Realtime API: low latency, interrupting the tutor.
- **Automatic end-of-utterance detection (VAD)** – instead of push-to-talk.
- **Accent choice in the profile** – US or UK voice per learner instead of one voice in `.env`.
- **Streaming replies** – stream the tutor's text and audio so the first words arrive within a few seconds.

## Quality

- **Tutor quality contract** – binary MUST/SHOULD checks with IDs and good/bad examples in a Markdown file, checking both the conversation and the returned data.
- **LLM judge** – score saved conversations against the quality contract (reasoning before each verdict).
- **Conversation simulator** – learner personas (levels, typical mistakes, Polish or one-word answers, injection attempts) talk to the tutor automatically; run before every prompt, schema or model change.
- **Choosing models by our own results** – compare chat models on the simulator and the judge (score, latency, cost) instead of public rankings.
- **Another tutor model** – e.g. Claude as an option.
