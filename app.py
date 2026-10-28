from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tutor.profiles import BrokenProfile, InvalidProfileId, Profile, list_profiles, load_profile, save_profile

app = FastAPI(title="SpeakUp")


class ProfileSummary(BaseModel):
    id: str
    name: str
    level: str


@app.exception_handler(InvalidProfileId)
def invalid_profile_id(request: Request, error: InvalidProfileId) -> JSONResponse:
    return JSONResponse({"detail": str(error)}, status_code=400)


@app.exception_handler(BrokenProfile)
def broken_profile(request: Request, error: BrokenProfile) -> JSONResponse:
    return JSONResponse({"detail": f"{error} Fix or delete the file."}, status_code=500)


@app.get("/api/profiles")
def get_profiles() -> list[ProfileSummary]:
    return [ProfileSummary(id=p.id, name=p.name, level=p.level) for p in list_profiles()]


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str) -> Profile:
    profile = load_profile(profile_id)
    if profile is None:
        raise HTTPException(404, "Profile not found.")
    return profile


@app.put("/api/profiles/{profile_id}")
def put_profile(profile_id: str, profile: Profile) -> Profile:
    if profile.id != profile_id:
        raise HTTPException(400, "Profile id in the body must match the URL.")
    return save_profile(profile)
