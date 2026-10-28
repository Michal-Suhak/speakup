import logging
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, ValidationError

from config import DEFAULT_LEVEL, PROFILES_DIR

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


class Profile(BaseModel):
    id: Annotated[str, StringConstraints(pattern=ID_PATTERN)]
    name: Name
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2"] = DEFAULT_LEVEL
    interests: list[Item] = Field(default_factory=lambda: list(DEFAULT_INTERESTS), max_length=20)
    goals: Text = ""
    avoid_topics: list[Item] = Field(default_factory=list, max_length=20)
    correction_style: Literal["gentle", "strict"] = "gentle"


def is_valid_id(profile_id: str) -> bool:
    return re.fullmatch(ID_PATTERN, profile_id) is not None


def _path(profile_id: str) -> Path:
    if not is_valid_id(profile_id):
        raise ValueError(f"Invalid profile id: {profile_id!r}")
    return PROFILES_DIR / f"{profile_id}.json"


def list_profiles() -> list[Profile]:
    profiles = []
    for path in sorted(PROFILES_DIR.glob("*.json")):
        try:
            profiles.append(Profile.model_validate_json(path.read_text(encoding="utf-8")))
        except ValidationError as error:
            log.warning("Skipping invalid profile %s: %s", path.name, error)
    return profiles


def load_profile(profile_id: str) -> Profile | None:
    path = _path(profile_id)
    if not path.exists():
        return None
    return Profile.model_validate_json(path.read_text(encoding="utf-8"))


def save_profile(profile: Profile) -> Profile:
    PROFILES_DIR.mkdir(exist_ok=True)
    _path(profile.id).write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    return profile
