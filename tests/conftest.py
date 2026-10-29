import pytest

from tutor import tts

MP3 = b"ID3 fake mp3"


class FakeSpeech:
    def __init__(self):
        self.calls = []
        self.error = None

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return type("Speech", (), {"content": MP3})()


@pytest.fixture(autouse=True)
def speech(monkeypatch):
    fake = FakeSpeech()
    client = type("Client", (), {"audio": type("Audio", (), {"speech": fake})()})()
    monkeypatch.setattr(tts, "get_client", lambda: client)
    return fake
