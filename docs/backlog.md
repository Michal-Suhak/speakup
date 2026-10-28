# Post-MVP backlog

Ideas to consider after the MVP ([0001](specs/0001-mvp.md)) is done. Just a list: no order, no commitment, no design.

To work on an item: discuss it, create a spec with the `feature-spec` skill, and remove the item from this list in the same PR (the spec takes over).

The backlog changes only through PRs, like everything on `main`. New ideas can be collected and added together in one "Update backlog" PR.

## Ideas

- **Session history and progress in SQLite** – save finished sessions and show progress over time; introduce SQLite (one local file) here, as the first feature that needs a database, and decide whether profiles move there too.
- **Vocabulary list with spaced repetition** – collect useful words from summaries and review them later; the tutor brings already learned words back into conversations.
- **Recurring mistakes across sessions** – detect mistakes the learner keeps making and practise them.
- **Roleplay scenes** – restaurant, hotel, airport, job interview.
- **Fast conversation mode** – OpenAI Realtime API: low latency, interrupting the tutor.
- **Automatic end-of-utterance detection (VAD)** – instead of push-to-talk.
- **Pronunciation assessment**
- **Another tutor model** – e.g. Claude as an option.
- **Login and internet deployment**

### Quality and evaluation

- **Tutor quality contract (leaderboard card)** – a Markdown file in git with binary yes/no checks for the tutor, each with an ID, a priority (MUST / SHOULD), the sessions it applies to, and good and bad examples. Starting points: corrects constructively and explains why (not only what), tells important from minor mistakes, prioritises communication over grammar, fits the learner's level, uses the learner's name and goal, encourages trying despite mistakes, celebrates progress, reacts sensibly to nonsense answers, does not offer features it does not have. Checks look at both the conversation and the returned data (corrections, summary JSON).
- **LLM judge** – a script that reads the quality contract, builds a Pydantic verdict model from it (for every check: reasoning first, then pass/fail), evaluates saved conversations and prints a score: MUST checks decide pass/fail, SHOULD checks the level (e.g. Silver / Gold / Diamond). Checks are grouped by area so one call does not have to judge everything.
- **Conversation simulator** – a second LLM plays learner personas (level, typical mistakes, mood, e.g. a stressed B1 learner, a C1 perfectionist with strict corrections, someone answering in one word or in Polish, a prompt-injection attempt) and talks to the tutor automatically; the conversations go to the LLM judge. Run it before every prompt, schema or model change and compare the scores.
- **Choosing the chat model by our own results** – run the simulator and the judge on several OpenAI models and pick by score, latency and cost instead of public rankings.

### Teaching

- **Self-correction first** – for an important mistake the tutor first gives a hint and lets the learner fix it themselves, and only then shows the correct form.
- **Streaming replies** – stream the tutor's text and audio so the first words arrive within a few seconds even for longer answers.
