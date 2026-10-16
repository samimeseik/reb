"""The design kernel: how organizations are built (forward), and which traces each
building block leaves (reverse). Loaded from YAML in this package."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from ..domain.errors import RebError
from ..domain.models import Component


class Text(BaseModel):
    en: str
    ar: str

    def get(self, language: str) -> str:
        return self.ar if language == "ar" else self.en


class Element(Text):
    id: str


class Trace(Text):
    element: str | None = None
    block: str | None = None
    strength: str  # strong | moderate | weak


class Block(BaseModel):
    id: str
    name: str
    name_ar: str
    purpose: str
    purpose_ar: str
    components: list[Component]
    elements: list[Element]
    rules: list[Text] = Field(default_factory=list)
    traces: list[Trace] = Field(default_factory=list)


class Family(BaseModel):
    id: str
    name: str
    name_ar: str
    blocks: dict[str, list[Text]] = Field(default_factory=dict)
    traces: list[Trace] = Field(default_factory=list)


class Rate(BaseModel):
    low: float
    high: float
    unit: str


class Equipment(BaseModel):
    id: str
    industry: str
    en: str
    ar: str
    function: str
    inputs: list[str]
    outputs: list[str]
    rate: Rate
    skill: str
    maintenance: str


def _dir() -> Path:
    return Path(str(resources.files(__package__)))


def _load(name: str) -> dict:
    return yaml.safe_load((_dir() / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def blocks() -> list[Block]:
    return [Block.model_validate(b) for b in _load("blocks.yaml")["blocks"]]


@lru_cache(maxsize=1)
def families() -> dict[str, Family]:
    return {f["id"]: Family.model_validate(f) for f in _load("families.yaml")["families"]}


@lru_cache(maxsize=1)
def equipment() -> dict[str, Equipment]:
    return {e["id"]: Equipment.model_validate(e) for e in _load("equipment.yaml")["equipment"]}


def family(family_id: str) -> Family:
    try:
        return families()[family_id]
    except KeyError:
        raise RebError("unknown_family", f"No family '{family_id}'. Families: {', '.join(families())}.") from None


def blocks_for_component(component: Component) -> list[Block]:
    return [b for b in blocks() if component in b.components]
