from openai import OpenAIError

import config
from tutor.llm import PROMPTS_DIR, LLMError, get_client, timed
from tutor.session import Usage

MIN_AUDIO_BYTES = 1000
MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_TRANSCRIPT_CHARS = 1000
# the API detects the format from the file extension: webm comes from Chrome, mp4 from Safari
FORMATS = {"webm": "audio/webm", "mp4": "audio/mp4", "m4a": "audio/mp4", "ogg": "audio/ogg", "wav": "audio/wav", "mp3": "audio/mpeg"}


class NoSpeech(Exception):
    pass


class RecordingTooLong(Exception):
    pass


class UnsupportedFormat(Exception):
    pass


def transcribe(audio: bytes, filename: str, usage: Usage) -> str:
    extension = filename.rpartition(".")[2].lower()
    if extension not in FORMATS:
        raise UnsupportedFormat(f"Unsupported recording format. Use one of: {', '.join(sorted(FORMATS))}.")
    if len(audio) < MIN_AUDIO_BYTES:
        raise NoSpeech("The recording is too short. Hold the button while you speak.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise RecordingTooLong("The recording is too long. Speak in shorter parts.")
    try:
        with timed("STT", config.STT_MODEL):
            transcription = get_client().audio.transcriptions.create(
                model=config.STT_MODEL,
                file=(f"turn.{extension}", audio, FORMATS[extension]),
                prompt=(PROMPTS_DIR / "transcribe.md").read_text(encoding="utf-8").strip(),
            )
    except OpenAIError as error:
        raise LLMError(f"Transcription failed ({type(error).__name__}). Try again in a moment.") from error
    # ponytail: only token-billed models are counted; whisper-1 reports seconds and would show as free
    if getattr(transcription, "usage", None) and transcription.usage.type == "tokens":
        usage.stt_input_tokens += transcription.usage.input_tokens
        usage.stt_output_tokens += transcription.usage.output_tokens
    text = transcription.text.strip()
    if not text:
        raise NoSpeech("No speech was recognised. Try again.")
    if len(text) > MAX_TRANSCRIPT_CHARS:
        raise RecordingTooLong("The recording is too long. Speak in shorter parts.")
    return text
