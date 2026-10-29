# Post-MVP backlog

Ideas to consider after the MVP ([0001](specs/0001-mvp.md)) is done. Just a list: no order, no commitment, no design.

To work on an item: discuss it, create a spec with the `feature-spec` skill, and remove the item from this list in the same PR (the spec takes over).

The backlog changes only through PRs, like everything on `main`. New ideas can be collected and added together in one "Update backlog" PR.

## Product

- **Session history and progress** – save finished sessions and show progress over time, in the database from the [online deployment draft](specs/online-deployment.md) (SQLite if that draft is rejected).
- **Admin panel in the browser** – accounts, limits and usage without the terminal commands from the online deployment draft, for when there are more learners.
- **Cleanup of abandoned sessions** – end sessions after e.g. 30 minutes without activity and log their cost, for when the browser's end call never arrives.
- **Memory for long conversations** – summarise older turns instead of cutting the history at the last 40 messages.

## Teaching

- **Vocabulary list with spaced repetition** – collect useful words from summaries, review them later and bring them back into conversations.
- **Recurring mistakes across sessions** – detect mistakes the learner keeps making and practise them.
- **Self-correction first** – for an important mistake, give a hint and let the learner fix it before showing the correct form.
- **Roleplay scenes** – restaurant, hotel, airport, job interview.
- **Pronunciation assessment**
- **Listening mode** – hide the tutor's text until the learner clicks, to practise understanding by ear.
- **"Jak powiedzieć…?"** – ask in Polish how to say a word during the conversation, without leaving the topic.

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
