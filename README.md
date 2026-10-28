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

The app arrives in the next stages. It will be started with:

```bash
uv run uvicorn app:app --reload
```
