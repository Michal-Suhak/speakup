import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BASE_DIR / "profiles"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
STT_MODEL = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-6-luna")
TTS_MODEL = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("TTS_VOICE", "marin")
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
DEFAULT_LEVEL = os.getenv("DEFAULT_LEVEL", "B1")
if DEFAULT_LEVEL not in LEVELS:
    sys.exit(f"DEFAULT_LEVEL in .env must be one of {', '.join(LEVELS)}, got {DEFAULT_LEVEL!r}.")


def require_api_key() -> str:
    if not OPENAI_API_KEY:
        sys.exit("OPENAI_API_KEY is missing. Copy .env.example to .env and set your key.")
    return OPENAI_API_KEY


def check_api_key() -> None:
    from openai import APIConnectionError, AuthenticationError, OpenAI

    client = OpenAI(api_key=require_api_key())
    try:
        client.models.list()
    except AuthenticationError:
        sys.exit("OpenAI rejected the key. Check OPENAI_API_KEY in .env.")
    except APIConnectionError:
        sys.exit("Cannot reach OpenAI. Check your internet connection.")
    print(f"OK: key works. Models: chat={CHAT_MODEL}, stt={STT_MODEL}, tts={TTS_MODEL} ({TTS_VOICE}).")


if __name__ == "__main__":
    check_api_key()
