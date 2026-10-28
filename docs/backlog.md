# Post-MVP backlog

Ideas to consider after the MVP ([0001](specs/0001-mvp.md)) is done. Just a list: no order, no commitment, no design.

To work on an item: discuss it, create a spec with the `feature-spec` skill, and remove the item from this list in the same PR (the spec takes over).

The backlog changes only through PRs, like everything on `main`. New ideas can be collected and added together in one "Update backlog" PR.

## Ideas

- **Session history and progress in SQLite** – save finished sessions and show progress over time; introduce SQLite (one local file) here, as the first feature that needs a database, and decide whether profiles move there too.
- **Vocabulary list with spaced repetition** – collect useful words from summaries and review them later.
- **Recurring mistakes across sessions** – detect mistakes the learner keeps making and practise them.
- **Roleplay scenes** – restaurant, hotel, airport, job interview.
- **Fast conversation mode** – OpenAI Realtime API: low latency, interrupting the tutor.
- **Automatic end-of-utterance detection (VAD)** – instead of push-to-talk.
- **Pronunciation assessment**
- **Another tutor model** – e.g. Claude as an option.
- **Login and internet deployment**
