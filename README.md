# SpeakUp

A local tutor for practising spoken English. You talk to it by voice, it answers, keeps the conversation going and corrects important mistakes. All models run through the OpenAI API.

> Work in progress. Current stage and plan: [docs/specs/0001-mvp.md](docs/specs/0001-mvp.md).

## Requirements

- macOS, Linux or Windows
- [uv](https://docs.astral.sh/uv/) (it installs a matching Python version itself)
- an OpenAI API key ([platform.openai.com](https://platform.openai.com/api-keys)); the API is billed separately from ChatGPT, so set a spending limit on your account

## Installation

1. Install uv (macOS / Linux):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   On macOS you can also use `brew install uv`.

2. Install the dependencies in the project folder:

   ```bash
   uv sync
   ```

3. Copy the settings file and put your key in `OPENAI_API_KEY`:

   ```bash
   cp env.example .env
   ```

   `.env` stays on your machine and is never committed.

## Running the tests

```bash
uv run pytest
```

## Checking the key

```bash
uv run python config.py
```

If everything works you will see `OK: key works`. Otherwise a message tells you what to fix (missing key, wrong key or no internet connection).

## Running

```bash
uv run uvicorn app:app --reload
```

Open http://localhost:8000, create your profile and pick a topic. Hold the button (or the space bar) while you speak, or type in the text field. The browser asks for microphone access the first time. The tutor answers by voice; click "powtórz" to hear the last answer again. Click "zakończ sesję" to get a summary with your main mistakes, useful words, a tip and the approximate cost of the session. The terminal shows how long each step (STT, LLM, TTS) took. The prices are in `config.py`; check them against the OpenAI pricing page when you change models. The voice is set with `TTS_VOICE` (see `env.example`).
