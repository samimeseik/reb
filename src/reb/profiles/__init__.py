"""Profiles are configuration on top of the generic engine: a checklist of
questions, the evidence grade each needs, the modes it may run in, and which
items become reconstruction obligations."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from ..domain.errors import RebError
from ..domain.models import Grade, Layer, Mode


class ProfileItem(BaseModel):
    id: str
    layer: Layer
    question: str
    question_ar: str | None = None
    required_grade: Grade = Grade.C
    obligation: bool = False
    cases: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)  # where the evidence usually is


class Profile(BaseModel):
    id: str
    name: str
    name_ar: str | None = None
    description: str
    allowed_modes: list[Mode]
    items: list[ProfileItem]

    def item(self, item_id: str) -> ProfileItem | None:
        return next((i for i in self.items if i.id == item_id), None)


def _builtin_dir() -> Path:
    return Path(str(resources.files(__package__)))


def list_profiles() -> list[Profile]:
    return [load_profile(p.stem) for p in sorted(_builtin_dir().glob("*.yaml"))]


def load_profile(name_or_path: str) -> Profile:
    path = Path(name_or_path)
    if not path.suffix:
        path = _builtin_dir() / f"{name_or_path}.yaml"
    if not path.exists():
        names = ", ".join(p.stem for p in _builtin_dir().glob("*.yaml"))
        raise RebError("unknown_profile", f"No profile '{name_or_path}'. Built-in profiles: {names}.")
    return Profile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
