import threading

import openai
import pytest
from fastapi.testclient import TestClient

from app import app
from tutor import llm, profiles, session, stt
from tutor.profiles import Profile, save_profile
from tutor.schemas import Correction, TutorTurn

AUDIO = b"\x1a" * 2000


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, "PROFILES_DIR", tmp_path / "profiles")
    monkeypatch.setattr(session, "_sessions", {})
    save_profile(Profile(id="michal", name="Michał", correction_style="strict"))

    def fake_ask(instructions, messages, *_):
        corrections = []
        if messages[-1].content == "I go there yesterday":
            corrections = [Correction(you_said="I go", better="I went", mistake_type="grammar", severity="important", explanation_pl="Czas przeszły.")]
        return TutorTurn(analysis="Notes.", corrections=corrections, reply="Nice?")

    monkeypatch.setattr(llm, "_ask", fake_ask)


class FakeTranscriptions:
    def __init__(self, result):
        self.result = result
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if isinstance(self.result, Exception):
            raise self.result
        return type("Transcription", (), {"text": self.result})()


@pytest.fixture
def transcriptions(monkeypatch):
    fake = FakeTranscriptions("I go there yesterday")
    client = type("Client", (), {"audio": type("Audio", (), {"transcriptions": fake})()})()
    monkeypatch.setattr(stt, "get_client", lambda: client)
    return fake


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session_id(client):
    return client.post("/api/session", json={"profile_id": "michal", "topic": "Travel"}).json()["session_id"]


def turn(client, session_id, audio=AUDIO, filename="turn.webm", content_type="audio/webm"):
    return client.post("/api/turn", data={"session_id": session_id}, files={"audio": (filename, audio, content_type)})


def test_voice_turn(client, session_id, transcriptions):
    response = turn(client, session_id)

    assert response.status_code == 200
    assert response.json() == {
        "user_text": "I go there yesterday",
        "reply": "Nice?",
        "corrections": [{"you_said": "I go", "better": "I went", "explanation_pl": "Czas przeszły."}],
        "audio": "SUQzIGZha2UgbXAz",
    }
    sent = transcriptions.kwargs
    assert sent["file"] == ("turn.webm", AUDIO, "audio/webm")
    assert "keeping their grammar mistakes" in sent["prompt"]
    assert "language" not in sent
    assert [m.content for m in session.get_session(session_id).messages][-2:] == ["I go there yesterday", "Nice?"]


def test_english_only_profile_sets_the_transcription_language(client, transcriptions):
    save_profile(Profile(id="michal", name="Michał", speech_language="en"))
    session_id = client.post("/api/session", json={"profile_id": "michal", "topic": "Travel"}).json()["session_id"]

    assert turn(client, session_id).status_code == 200
    assert transcriptions.kwargs["language"] == "en"


def test_safari_recording_keeps_mp4_extension(client, session_id, transcriptions):
    assert turn(client, session_id, filename="recording.MP4", content_type="text/html").status_code == 200
    assert transcriptions.kwargs["file"] == ("turn.mp4", AUDIO, "audio/mp4")


@pytest.mark.parametrize(
    ("kwargs", "status"),
    [
        ({"audio": b"x" * 10}, 400),
        ({"filename": "turn.exe"}, 415),
        ({"filename": "turn"}, 415),
    ],
)
def test_bad_recording_never_calls_the_api(client, session_id, transcriptions, kwargs, status):
    assert turn(client, session_id, **kwargs).status_code == status
    assert transcriptions.kwargs is None


def test_too_large_recording_is_413(client, session_id, transcriptions, monkeypatch):
    monkeypatch.setattr(stt, "MAX_AUDIO_BYTES", 1500)
    assert turn(client, session_id).status_code == 413
    assert transcriptions.kwargs is None


@pytest.mark.parametrize(("text", "status"), [("   ", 400), ("a" * 1001, 413)])
def test_unusable_transcript(client, session_id, transcriptions, text, status):
    transcriptions.result = text
    assert turn(client, session_id).status_code == status
    assert len(session.get_session(session_id).messages) == 1


def test_transcription_error_is_502_without_provider_text(client, session_id, transcriptions):
    transcriptions.result = openai.OpenAIError("secret provider detail")
    response = turn(client, session_id)

    assert response.status_code == 502
    assert "secret provider detail" not in response.text


def test_unknown_session_is_404(client, transcriptions):
    assert turn(client, "missing").status_code == 404
    assert transcriptions.kwargs is None


def test_busy_session_is_409_before_transcribing(client, session_id, transcriptions):
    with session.get_session(session_id).turn():
        result = {}
        worker = threading.Thread(target=lambda: result.setdefault("response", turn(client, session_id)))
        worker.start()
        worker.join()

    assert result["response"].status_code == 409
    assert transcriptions.kwargs is None
