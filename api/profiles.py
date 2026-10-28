from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tutor.profiles import Profile, list_profiles, load_profile, save_profile

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


class ProfileSummary(BaseModel):
    id: str
    name: str
    level: str


@router.get("")
def get_profiles() -> list[ProfileSummary]:
    return [ProfileSummary(id=p.id, name=p.name, level=p.level) for p in list_profiles()]


@router.get("/{profile_id}")
def get_profile(profile_id: str) -> Profile:
    profile = load_profile(profile_id)
    if profile is None:
        raise HTTPException(404, "Profile not found.")
    return profile


@router.put("/{profile_id}")
def put_profile(profile_id: str, profile: Profile) -> Profile:
    if profile.id != profile_id:
        raise HTTPException(400, "Profile id in the body must match the URL.")
    return save_profile(profile)
