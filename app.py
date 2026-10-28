from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tutor.profiles import Profile, is_valid_id, list_profiles, load_profile, save_profile

app = FastAPI(title="SpeakUp")


class ProfileSummary(BaseModel):
    id: str
    name: str
    level: str


def _check_id(profile_id: str) -> None:
    if not is_valid_id(profile_id):
        raise HTTPException(400, "Invalid profile id: use 1-32 lowercase letters, digits or hyphens.")


@app.get("/api/profiles")
def get_profiles() -> list[ProfileSummary]:
    return [ProfileSummary(id=p.id, name=p.name, level=p.level) for p in list_profiles()]


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str) -> Profile:
    _check_id(profile_id)
    profile = load_profile(profile_id)
    if profile is None:
        raise HTTPException(404, "Profile not found.")
    return profile


@app.put("/api/profiles/{profile_id}")
def put_profile(profile_id: str, profile: Profile) -> Profile:
    _check_id(profile_id)
    if profile.id != profile_id:
        raise HTTPException(400, "Profile id in the body must match the URL.")
    return save_profile(profile)
