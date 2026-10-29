import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Literal

from tutor.profiles import Profile


class SessionNotFound(Exception):
    pass


class SessionBusy(Exception):
    pass


@dataclass
class Message:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class Session:
    profile: Profile
    topic: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    messages: list[Message] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @contextmanager
    def turn(self) -> Iterator[None]:
        if not self._lock.acquire(blocking=False):
            raise SessionBusy("The tutor is still answering the previous message.")
        try:
            yield
        finally:
            self._lock.release()


_sessions: dict[str, Session] = {}


# ponytail: sessions live until the server stops; stage 4 removes them when a session ends
def register_session(session: Session) -> None:
    _sessions[session.id] = session


def get_session(session_id: str) -> Session:
    session = _sessions.get(session_id)
    if session is None:
        raise SessionNotFound("Session not found. Start a new session.")
    return session
