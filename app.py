from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api import profiles, sessions
from tutor.llm import LLMError, LLMUnavailable
from tutor.profiles import BrokenProfile, InvalidProfileId
from tutor.session import SessionBusy, SessionNotFound

app = FastAPI(title="SpeakUp")
app.include_router(profiles.router)
app.include_router(sessions.router)

ERROR_STATUS = {
    InvalidProfileId: 400,
    BrokenProfile: 400,
    SessionNotFound: 404,
    SessionBusy: 409,
    LLMError: 502,
    LLMUnavailable: 503,
}


def _error_response(request: Request, error: Exception) -> JSONResponse:
    status = next(code for error_type, code in ERROR_STATUS.items() if isinstance(error, error_type))
    return JSONResponse({"detail": str(error)}, status_code=status)


for error_type in ERROR_STATUS:
    app.add_exception_handler(error_type, _error_response)
