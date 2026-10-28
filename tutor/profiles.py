import logging
import os
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, ValidationError

from config import DEFAULT_LEVEL, LEVELS, PROFILES_DIR

log = logging.getLogger(__name__)

ID_PATTERN = r"^[a-z0-9-]{1,32}$"
DEFAULT_INTERESTS = [
    "Travel",
    "Work",
    "Hobbies",
    "Food",
    "Movies & Books",
    "Daily routine",
    "Technology",
    "Job interview",
]

Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Item = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


class InvalidProfileId(ValueError):
    pass


class BrokenProfile(Exception):
    pass


class Profile(BaseModel):
    id: Annotated[str, StringConstraints(pattern=ID_PATTERN)]
    name: Name
    level: Literal[LEVELS] = DEFAULT_LEVEL
    interests: list[Item] = Field(default_factory=lambda: list(DEFAULT_INTERESTS), max_length=20)
    goals: Text = ""
    avoid_topics: list[Item] = Field(default_factory=list, max_length=20)
    correction_style: Literal["gentle", "strict"] = "gentle"


def _path(profile_id: str) -> Path:
    if not re.fullmatch(ID_PATTERN, profile_id):
        raise InvalidProfileId("Invalid profile id: use 1-32 lowercase letters, digits or hyphens.")
    return PROFILES_DIR / f"{profile_id}.json"


def _read(path: Path) -> Profile:
    try:
        profile = Profile.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError) as error:
        raise BrokenProfile(
            f"profiles/{path.name} is not a valid profile ({type(error).__name__}). Fix or delete the file."
        ) from None
    if profile.id != path.stem:
        raise BrokenProfile(
            f"profiles/{path.name} contains id {profile.id!r}; the id must match the file name. Fix or delete the file."
        )
    return profile


def list_profiles() -> list[Profile]:
    profiles = []
    for path in sorted(PROFILES_DIR.glob("*.json")):
        try:
            profiles.append(_read(path))
        except BrokenProfile as error:
            log.warning("Skipping profile: %s", error)
    return profiles


def load_profile(profile_id: str) -> Profile | None:
    path = _path(profile_id)
    return _read(path) if path.exists() else None


def save_profile(profile: Profile) -> Profile:
    path = _path(profile.id)
    PROFILES_DIR.mkdir(exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return profile
