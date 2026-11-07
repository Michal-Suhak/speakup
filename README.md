# SpeakUp

A local tutor for practising spoken English. You talk to it by voice, it answers, keeps the conversation going and corrects important mistakes. All models run through the OpenAI API.

> Work in progress. Current stage and plan: [docs/specs/0001-mvp.md](docs/specs/0001-mvp.md).

## Requirements

- macOS, Linux or Windows
- [uv](https://docs.astral.sh/uv/) (it installs a matching Python version itself)
- an OpenAI API key ([platform.openai.com](https://platform.openai.com/api-keys)); the API is billed separately from ChatGPT, so set a spending limit on your account

## Windows: one click

1. Download [start.cmd](https://github.com/Michal-Suhak/speakup/raw/main/start.cmd) and save it on the desktop.
2. Double-click it. If Windows shows "Windows protected your PC", click "More info" → "Run anyway".
3. The first start installs uv and Python (a few minutes) and asks for the OpenAI key once. Then the browser opens SpeakUp.

Every start downloads the latest version from GitHub into `%USERPROFILE%\SpeakUp`; the key (`.env`) and the profiles stay. Close the black window to stop SpeakUp. A wrong key is rejected at the first start; to change the key later, delete `%USERPROFILE%\SpeakUp\.env` and start again.

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

Open http://localhost:8000, create your profile and pick a topic. Hold the button (or the space bar) while you speak, or type in the text field. The browser asks for microphone access the first time. If your speech comes out as Polish-looking words, set "Rozpoznawanie mowy" in the profile to "zawsze po angielsku". The tutor answers by voice; click "powtórz" to hear the last answer again, or "wolniej" to hear it at a slower speed. Click "przetłumacz" under a tutor line to see it in Polish (shown by default at A1–A2). Click "zakończ sesję" to get a summary with your main mistakes, useful words, a tip and the approximate cost of the session. The terminal shows how long each step (STT, LLM, TTS) took. The prices are in `config.py`; check them against the OpenAI pricing page when you change models. The voice is set with `TTS_VOICE` (see `env.example`).
