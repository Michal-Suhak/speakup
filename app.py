from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api import profiles
from tutor.profiles import BrokenProfile, InvalidProfileId

app = FastAPI(title="SpeakUp")
app.include_router(profiles.router)


@app.exception_handler(InvalidProfileId)
def invalid_profile_id(request: Request, error: InvalidProfileId) -> JSONResponse:
    return JSONResponse({"detail": str(error)}, status_code=400)


@app.exception_handler(BrokenProfile)
def broken_profile(request: Request, error: BrokenProfile) -> JSONResponse:
    return JSONResponse({"detail": f"{error} Fix or delete the file."}, status_code=400)
