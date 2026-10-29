from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
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


@app.exception_handler(RequestValidationError)
def invalid_request(request: Request, error: RequestValidationError) -> JSONResponse:
    # FastAPI's default 422 body echoes the submitted value, which may be a learner message or profile text
    detail = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in error.errors()]
    return JSONResponse({"detail": detail}, status_code=422)
