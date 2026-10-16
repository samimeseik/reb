"""Archetypes: typical operating models, composed from pattern modules on three
axes (how value is created, how it is delivered, who pays) plus a family from
the design kernel. Applying an archetype seeds a full starting blueprint in which
every element is a LOW-confidence hypothesis until traces support it."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from ..domain.errors import RebError
from ..domain.ledger import Ledger
from ..domain.models import Component, DesignKind, HypothesisBasis
from ..kernel import Rate, Text, equipment, family


class PatternStatement(Text):
    impact: str = "medium"
    test: str | None = None
    range: Rate | None = None


class FailurePoint(Text):
    component: Component


class Signal(BaseModel):
    component: Component
    signal: str
    suggests: str


class Module(BaseModel):
    id: str
    name: str
    name_ar: str
    components: dict[Component, list[PatternStatement]] = Field(default_factory=dict)
    failure_points: list[FailurePoint] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)


class BuildStep(Text):
    component: Component
    phase: str | None = None


class Archetype(BaseModel):
    id: str
    family: str
    name: str
    name_ar: str
    compose: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    processes: list[Text] = Field(default_factory=list)
    roles: list[Text] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    components: dict[Component, list[PatternStatement]] = Field(default_factory=dict)
    build: list[BuildStep] = Field(default_factory=list)


def _dir() -> Path:
    return Path(str(resources.files(__package__)))


@lru_cache(maxsize=1)
def modules() -> dict[str, Module]:
    out: dict[str, Module] = {}
    for path in sorted((_dir() / "modules").glob("*.yaml")):
        for m in yaml.safe_load(path.read_text(encoding="utf-8"))["modules"]:
            out[m["id"]] = Module.model_validate(m)
    return out


@lru_cache(maxsize=1)
def archetypes() -> dict[str, Archetype]:
    data = yaml.safe_load((_dir() / "composites.yaml").read_text(encoding="utf-8"))
    out = {a["id"]: Archetype.model_validate(a) for a in data["archetypes"]}
    for a in out.values():  # fail fast on broken references
        family(a.family)
        for mid in a.compose:
            if mid not in modules():
                raise RebError("unknown_module", f"Archetype {a.id} composes unknown module {mid}.")
        for eid in a.equipment:
            if eid not in equipment():
                raise RebError("unknown_equipment", f"Archetype {a.id} lists unknown equipment {eid}.")
    return out


def archetype(archetype_id: str) -> Archetype:
    try:
        return archetypes()[archetype_id]
    except KeyError:
        raise RebError(
            "unknown_archetype", f"No archetype '{archetype_id}'. Archetypes: {', '.join(archetypes())}."
        ) from None


def suggest(text: str) -> list[dict[str, Any]]:
    """Rank archetypes by keyword hits in a description (name, site title, about text)."""
    low = text.casefold()
    scored = []
    for a in archetypes().values():
        hits = [k for k in a.keywords if k.casefold() in low]
        if hits:
            scored.append({"archetype": a.id, "name": a.name, "name_ar": a.name_ar, "hits": hits})
    return sorted(scored, key=lambda s: -len(s["hits"]))


def apply_archetype(ledger: Ledger, archetype_id: str, *, extra_modules: list[str] | None = None) -> dict[str, Any]:
    """Seed the starting blueprint. Everything created here is basis=archetype
    (confidence low) and carries the cheapest test that would confirm it."""
    a = archetype(archetype_id)
    lang = ledger.engagement.language
    created: dict[str, list[str]] = {"hypotheses": [], "design": []}
    first_by_component: dict[Component, str] = {}

    def add(component: Component, text: str, *, test: str | None, impact: str = "medium",
            rng: Rate | None = None) -> str:
        h = ledger.add_hypothesis(
            statement=text,
            component=component,
            basis=HypothesisBasis.ARCHETYPE,
            archetype=a.id,
            assumptions=[f"Typical for: {a.name}"],
            range=rng.model_dump() if rng else None,
            test=test,
            impact=impact,
        )
        created["hypotheses"].append(h.id)
        first_by_component.setdefault(component, h.id)
        return h.id

    module_ids = [*a.compose, *(extra_modules or [])]
    for mid in module_ids:
        if mid not in modules():
            raise RebError("unknown_module", f"No module '{mid}'.")
    for mid in module_ids:
        for component, items in modules()[mid].components.items():
            for st in items:
                add(component, st.get(lang), test=st.test, impact=st.impact, rng=st.range)
    for component, items in a.components.items():
        for st in items:
            add(component, st.get(lang), test=st.test, impact=st.impact, rng=st.range)
    if a.processes:
        arrow = " ← " if lang == "ar" else " → "
        add(Component.OPERATIONS, arrow.join(p.get(lang) for p in a.processes),
            test="Map one real case end to end and compare the stages.", impact="high")
    if a.roles:
        sep = "، " if lang == "ar" else ", "
        add(Component.TEAM, sep.join(r.get(lang) for r in a.roles),
            test="Compare with the team page, job ads and the people seen in public.", impact="medium")
    for eid in a.equipment:
        eq = equipment()[eid]
        name = eq.ar if lang == "ar" else eq.en
        add(Component.ASSETS, f"{name}: {eq.function}", test="Look for it in photos/videos and read the nameplate.",
            impact="medium", rng=eq.rate)
    fam = family(a.family)
    for block_id, notes in fam.blocks.items():
        from ..kernel import blocks as kernel_blocks

        block = next(b for b in kernel_blocks() if b.id == block_id)
        for note in notes:
            add(block.components[0], note.get(lang), test=None, impact="medium")
    for mid in module_ids:
        for fp in modules()[mid].failure_points:
            ref = first_by_component.get(fp.component) or created["hypotheses"][0]
            d = ledger.add_design_item(component=fp.component, kind=DesignKind.IMPROVE, statement=fp.get(lang), refs=[ref])
            created["design"].append(d.id)
    for step in a.build:
        ref = first_by_component.get(step.component) or created["hypotheses"][0]
        d = ledger.add_design_item(component=step.component, kind=DesignKind.BUILD_STEP, statement=step.get(lang),
                                   refs=[ref], phase=step.phase)
        created["design"].append(d.id)
    ledger.data.archetype = a.id
    return {"archetype": a.id, "family": a.family, **{k: len(v) for k, v in created.items()}, "ids": created}


def signal_hints(archetype_id: str) -> list[dict[str, str]]:
    """Which public traces to look for, for this archetype (from its modules)."""
    a = archetype(archetype_id)
    hints = []
    for mid in a.compose:
        for s in modules()[mid].signals:
            hints.append({"component": s.component.value, "signal": s.signal, "suggests": s.suggests})
    for t in family(a.family).traces:
        hints.append({"component": t.block or "", "signal": t.en, "suggests": f"strength: {t.strength}"})
    return hints
