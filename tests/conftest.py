import pytest

from tutor import tts

class FakeSpeech:
    def __init__(self):
        self.calls = []
        self.error = None
        self.content = b"ID3 fake mp3"

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return type("Speech", (), {"content": self.content})()


@pytest.fixture(autouse=True)
def speech(monkeypatch):
    fake = FakeSpeech()
    client = type("Client", (), {"audio": type("Audio", (), {"speech": fake})()})()
    monkeypatch.setattr(tts, "get_client", lambda: client)
    return fake
