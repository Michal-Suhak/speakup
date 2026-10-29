import logging
from types import SimpleNamespace as obj

import pytest

import config
from tutor import llm, stt, tts
from tutor.schemas import TutorTurn
from tutor.session import Message, Usage


def test_cost_uses_config_rates(monkeypatch):
    for name, rate in [
        ("CHAT_INPUT_USD_PER_1M_TOKENS", 1),
        ("CHAT_OUTPUT_USD_PER_1M_TOKENS", 2),
        ("STT_INPUT_USD_PER_1M_TOKENS", 3),
        ("STT_OUTPUT_USD_PER_1M_TOKENS", 4),
        ("TTS_USD_PER_1M_CHARACTERS", 5),
    ]:
        monkeypatch.setattr(config, name, rate)
    usage = Usage(chat_input_tokens=1_000_000, chat_output_tokens=500_000, stt_input_tokens=0, stt_output_tokens=250_000, tts_characters=200_000)

    assert usage.cost_usd() == pytest.approx(1 + 1 + 1 + 1)


def test_chat_usage_and_timing_are_recorded(monkeypatch, caplog):
    turn = TutorTurn(analysis="", corrections=[], reply="Hi?")
    response = obj(output_parsed=turn, usage=obj(input_tokens=120, output_tokens=30))
    responses = obj(parse=lambda **kwargs: response)
    monkeypatch.setattr(llm, "get_client", lambda: obj(responses=responses))
    usage = Usage()

    with caplog.at_level(logging.INFO, logger="tutor"):
        llm._ask("instructions", [Message("user", "Hi")], usage)
        llm._ask("instructions", [Message("user", "Hi")], usage)

    assert (usage.chat_input_tokens, usage.chat_output_tokens) == (240, 60)
    assert "LLM took" in caplog.text and config.CHAT_MODEL in caplog.text


@pytest.mark.parametrize(
    ("reported", "expected"),
    [
        (obj(type="tokens", input_tokens=50, output_tokens=10), (50, 10)),
        (obj(type="duration", seconds=3), (0, 0)),
        (None, (0, 0)),
    ],
)
def test_stt_usage(monkeypatch, reported, expected):
    transcriptions = obj(create=lambda **kwargs: obj(text="Hello", usage=reported))
    monkeypatch.setattr(stt, "get_client", lambda: obj(audio=obj(transcriptions=transcriptions)))
    usage = Usage()

    stt.transcribe(b"x" * 2000, "turn.webm", usage)

    assert (usage.stt_input_tokens, usage.stt_output_tokens) == expected


def test_tts_counts_characters_only_when_it_works(speech):
    import openai

    usage = Usage()
    tts.synthesize("Hello there", "B1", usage)
    speech.error = openai.OpenAIError("down")
    tts.synthesize("Not spoken", "B1", usage)

    assert usage.tts_characters == len("Hello there")
