from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StringConstraints

from tutor import llm
from tutor.profiles import load_profile
from tutor.session import Session, get_session, register_session

router = APIRouter(prefix="/api", tags=["sessions"])

Topic = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
UserText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class StartRequest(BaseModel):
    profile_id: str
    topic: Topic


class StartResponse(BaseModel):
    session_id: str
    reply: str


class TextRequest(BaseModel):
    session_id: str
    text: UserText


class CorrectionOut(BaseModel):
    you_said: str
    better: str
    explanation_pl: str


class TurnResponse(BaseModel):
    reply: str
    corrections: list[CorrectionOut]


@router.post("/session")
def start_session(request: StartRequest) -> StartResponse:
    profile = load_profile(request.profile_id)
    if profile is None:
        raise HTTPException(404, "Profile not found.")
    session = Session(profile=profile, topic=request.topic)
    turn = llm.start(session)
    register_session(session)
    return StartResponse(session_id=session.id, reply=turn.reply)


@router.post("/text")
def text_turn(request: TextRequest) -> TurnResponse:
    turn = llm.reply(get_session(request.session_id), request.text)
    return TurnResponse.model_validate(turn, from_attributes=True)
