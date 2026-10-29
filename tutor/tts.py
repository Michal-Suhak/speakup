import logging
from string import Template

from openai import OpenAIError

import config
from tutor.llm import PROMPTS_DIR, get_client, timed
from tutor.session import Usage

log = logging.getLogger(__name__)


def synthesize(text: str, level: str, usage: Usage) -> bytes | None:
    """The reply as mp3, or None when TTS fails, so the turn still returns its text."""
    instructions = Template((PROMPTS_DIR / "speak.md").read_text(encoding="utf-8")).substitute(level=level)
    try:
        with timed(log, "TTS", config.TTS_MODEL):
            speech = get_client().audio.speech.create(
                model=config.TTS_MODEL,
                voice=config.TTS_VOICE,
                input=text,
                instructions=instructions.strip(),
                response_format="mp3",
            )
    except OpenAIError as error:
        log.warning("TTS failed (%s), sending the reply without audio", type(error).__name__)
        return None
    usage.tts_characters += len(text)
    return speech.content
