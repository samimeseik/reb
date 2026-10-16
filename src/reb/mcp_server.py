"""MCP stdio server. Each tool takes the engagement `workspace` (default: the
REB_WORKSPACE environment variable, else the current directory) and returns
structured results, including evidence ids, grades and limitations."""

from __future__ import annotations

import functools
import json
import os
from pathlib import Path
from typing import Any

from .application import analysis, coverage, ingest, report
from .domain.errors import RebError
from .domain.ledger import Ledger
from .profiles import list_profiles as _list_profiles
from .profiles import load_profile

INSTRUCTIONS = """REB reverse-engineers how an organization actually works, with evidence.
Rules: (1) open_engagement first; its mode decides which sources are admissible.
(2) ingest_source each file; read_source to see its pseudonymized text with line numbers.
(3) record_evidence for each fact you use, quoting the source verbatim — quotes are checked.
(4) record_claim only with evidence ids; a claim without evidence is shown as conjecture.
(5) When something is not covered, record_unknown — missing coverage is unknown, not absent.
(6) Never fill gaps with industry-typical stories; mark industry_prior=true if you must.
(7) Use grades and statuses, never words like verified/guaranteed/مضمون/موثّق."""


def _ws(workspace: str | None) -> Path:
    return Path(workspace or os.environ.get("REB_WORKSPACE") or ".").expanduser()


def _safe(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except RebError as err:
            return err.to_dict()
        except ValueError as exc:  # includes pydantic ValidationError
            return {"error": "invalid_input", "message": str(exc).splitlines()[0] if str(exc) else repr(exc)}

    return wrapper


def _dump(obj: Any) -> Any:
    return json.loads(obj.model_dump_json()) if hasattr(obj, "model_dump_json") else obj


def build_server():
    try:  # mcp >= 2
        from mcp.server.mcpserver import MCPServer as Server
    except ImportError:
        try:  # mcp 1.x
            from mcp.server.fastmcp import FastMCP as Server
        except ImportError as exc:  # pragma: no cover
            raise SystemExit("The MCP server needs the 'mcp' extra: pip install 'reb-agents[mcp]'") from exc

    server = Server("reb", instructions=INSTRUCTIONS)

    @server.tool()
    @_safe
    def list_profiles() -> list[dict]:
        """List built-in analysis profiles (checklists) and the modes they allow."""
        return [
            {"id": p.id, "name": p.name, "name_ar": p.name_ar, "description": p.description,
             "modes": [m.value for m in p.allowed_modes], "items": [i.id for i in p.items]}
            for p in _list_profiles()
        ]

    @server.tool()
    @_safe
    def open_engagement(
        name: str, subject: str, mode: str, authorization: str | None = None,
        profile: str | None = None, language: str = "ar", workspace: str | None = None,
        aliases: list[str] | None = None,
    ) -> dict:
        """Open an engagement. mode: self (you own/run it), engaged (written mandate from the
        organization), public (public sources only). authorization is required unless public.
        aliases: the subject's other names and web domains; sources from them are never
        counted as independent of the subject."""
        if profile:
            prof = load_profile(profile)
            if mode not in [m.value for m in prof.allowed_modes]:
                raise RebError("mode_not_allowed", f"Profile '{prof.id}' allows {[m.value for m in prof.allowed_modes]}.")
        led = Ledger.init(_ws(workspace), name=name, subject=subject, mode=mode,
                          authorization=authorization, profile=profile, language=language,
                          aliases=aliases)
        return _dump(led.engagement)

    @server.tool()
    @_safe
    def ingest_source(
        path: str, custody: str, origin_party: str, controller: str | None = None,
        kind: str | None = None, title: str | None = None, legal_basis: str | None = None,
        sensitivity: str = "internal", language: str | None = None,
        upstream_ids: list[str] | None = None, verification_ids: list[str] | None = None,
        independent_channel: bool = False, site: str | None = None, period_start: str | None = None,
        period_end: str | None = None, notes: str | None = None, workspace: str | None = None,
    ) -> dict:
        """Register a source file (PDF, DOCX, TXT, CSV/XLSX, e-invoice XML, WhatsApp export,
        image, interview audio/transcript) and extract its inventory facts.
        custody: subject_held | issuer_verifiable | third_party | captured_live | public.
        Interviews and chat exports need legal_basis (consent reference); public sources need
        their URL in legal_basis; issuer_verifiable needs verification_ids (the ingested issuer check).
        controller: who controls the content. The organization's own staff/documents/systems are
        forced to one controller. period_start/period_end (YYYY-MM-DD) bound what the source covers."""
        with Ledger.open(_ws(workspace), write=True) as led:
            return ingest.ingest_file(
                led, path, custody=custody, origin_party=origin_party,
                controller=controller, kind=kind, title=title, legal_basis=legal_basis,
                sensitivity=sensitivity, language=language, upstream_ids=upstream_ids,
                verification_ids=verification_ids, independent_channel=independent_channel,
                context={"site": site, "period_start": period_start, "period_end": period_end}, notes=notes,
            )

    @server.tool()
    @_safe
    def read_source(source_id: str, start_line: int = 1, max_lines: int = 200, skip_boilerplate: bool = False,
                    workspace: str | None = None) -> dict:
        """Read a source's stored (pseudonymized) text with line numbers, for quoting.
        skip_boilerplate hides menus/footers repeated across the same site's pages."""
        with Ledger.open(_ws(workspace), write=False) as led:
            return ingest.read_source(led, source_id, start_line=start_line, max_lines=max_lines,
                                      skip_boilerplate=skip_boilerplate)

    @server.tool()
    @_safe
    def record_observation(
        title: str, note: str, observer_role: str, legal_basis: str | None = None, site: str | None = None, when: str | None = None,
        shift: str | None = None, facts: list[dict] | None = None, public_premises: bool = False,
        workspace: str | None = None,
    ) -> dict:
        """Record what you directly observed on site (site walk, time study, nameplate reading).
        facts: [{"fact": "...", "layer": "...", "entity": "...", "location": "..."}].
        Observing staff needs legal_basis (e.g. staff notice), unless public_premises=true."""
        with Ledger.open(_ws(workspace), write=True) as led:
            return ingest.record_observation(
                led, title=title, note=note, observer_role=observer_role, legal_basis=legal_basis,
                site=site, when=when, shift=shift, facts=facts, public_premises=public_premises,
            )

    @server.tool()
    @_safe
    def record_evidence(
        source_id: str, fact: str, authority: str, location: str | None = None,
        quote: str | None = None, confidence: str = "observed", entity: str | None = None,
        layer: str | None = None, as_of: str | None = None, workspace: str | None = None,
    ) -> dict:
        """Record one fact from a source. authority: system_record | direct_observation |
        governing_document | public_record | testimony | public_signal | analyst_inference.
        The quote must appear verbatim in the source text. The grade is computed, not chosen."""
        with Ledger.open(_ws(workspace), write=True) as led:
            ev = led.add_evidence(source_id=source_id, fact=fact, authority=authority, location=location,
                                  quote=quote, confidence=confidence, entity=entity, layer=layer, as_of=as_of)
            return _dump(ev)

    @server.tool()
    @_safe
    def record_claim(
        statement: str, layer: str, evidence_ids: list[str] | None = None,
        contradicting_evidence_ids: list[str] | None = None, entity: str | None = None,
        item: str | None = None, kind: str = "neutral", metric: str | None = None,
        value: float | None = None, unit: str | None = None, replicability: str = "unassessed",
        industry_prior: bool = False, as_of: str | None = None, component: str | None = None,
        workspace: str | None = None,
    ) -> dict:
        """Record a claim about the organization. Status (conjecture / single_source /
        triangulated / contradicted) and grade are computed from the evidence.
        kind=stated|enacted with metric+value enables compare_stated_vs_enacted.
        layer: strategy|revenue|customer|operations|equipment|systems|people|supply|finance|regulation|culture"""
        with Ledger.open(_ws(workspace), write=True) as led:
            c = led.record_claim(statement=statement, layer=layer, evidence_ids=evidence_ids,
                                 contradicting_evidence_ids=contradicting_evidence_ids, entity=entity, item=item,
                                 kind=kind, metric=metric, value=value, unit=unit,
                                 replicability=replicability, industry_prior=industry_prior, as_of=as_of,
                                 component=component)
            return _dump(c)

    @server.tool()
    @_safe
    def record_unknown(
        question: str, layer: str | None = None, entity: str | None = None, item: str | None = None,
        required_authority: str | None = None, recommended_probes: list[str] | None = None,
        supporting_evidence_ids: list[str] | None = None, contradicting_evidence_ids: list[str] | None = None,
        workspace: str | None = None,
    ) -> dict:
        """Record an open question and the cheapest probe that would settle it."""
        with Ledger.open(_ws(workspace), write=True) as led:
            u = led.record_unknown(question=question, layer=layer, entity=entity, item=item,
                                   required_authority=required_authority, recommended_probes=recommended_probes,
                                   supporting_evidence_ids=supporting_evidence_ids,
                                   contradicting_evidence_ids=contradicting_evidence_ids)
            return _dump(u)

    @server.tool()
    @_safe
    def update_unknown(
        unknown_id: str, revision: int, status: str | None = None,
        add_supporting: list[str] | None = None, add_contradicting: list[str] | None = None,
        add_probes: list[str] | None = None, resolution: dict | None = None, workspace: str | None = None,
    ) -> dict:
        """Update an unknown at its current revision. Resolving needs
        resolution={"kind": "verified|refuted|out_of_scope", "evidence_ids": [...]}."""
        with Ledger.open(_ws(workspace), write=True) as led:
            u = led.update_unknown(unknown_id, revision=revision, status=status, add_supporting=add_supporting,
                                   add_contradicting=add_contradicting, add_probes=add_probes, resolution=resolution)
            return _dump(u)

    @server.tool()
    @_safe
    def search_evidence(
        text: str | None = None, layer: str | None = None, entity: str | None = None,
        min_grade: str | None = None, workspace: str | None = None,
    ) -> list[dict]:
        """Find recorded evidence by text, layer, entity or minimum grade."""
        with Ledger.open(_ws(workspace), write=False) as led:
            from .domain.grading import GRADE_ORDER
            out = []
            for ev in led.data.evidence.values():
                if text and text.casefold() not in ev.fact.casefold():
                    continue
                if layer and (ev.layer is None or ev.layer.value != layer):
                    continue
                if entity and ev.entity != entity:
                    continue
                if min_grade and GRADE_ORDER.index(ev.grade) > GRADE_ORDER.index(min_grade):
                    continue
                out.append({"id": ev.id, "grade": ev.grade.value, "fact": ev.fact, "source_id": ev.source_id,
                            "location": ev.location, "authority": ev.authority.value})
            return out

    @server.tool()
    @_safe
    def analyze_event_log(
        source_id: str, case_column: str | None = None, activity_column: str | None = None,
        time_column: str | None = None, activity_map: dict[str, list[str]] | None = None,
        case_pattern: str | None = None, entity: str | None = None, workspace: str | None = None,
    ) -> dict:
        """Process mining: variants, directly-follows graph (with Mermaid), cycle times, rework.
        Tables: give case/activity/time columns. Chat exports: give activity_map and case_pattern."""
        with Ledger.open(_ws(workspace), write=True) as led:
            return analysis.analyze_event_log(
                led, source_id, case_column=case_column, activity_column=activity_column,
                time_column=time_column, activity_map=activity_map, case_pattern=case_pattern, entity=entity,
            )

    @server.tool()
    @_safe
    def analyze_invoices(source_ids: list[str], direction: str = "sales", workspace: str | None = None) -> dict:
        """Revenue (sales) or spend (purchases) concentration across e-invoice sources."""
        with Ledger.open(_ws(workspace), write=True) as led:
            return analysis.analyze_invoices(led, source_ids, direction=direction)

    @server.tool()
    @_safe
    def compare_stated_vs_enacted(metric: str, entity: str | None = None, tolerance: float = 0.15,
                                  workspace: str | None = None) -> dict:
        """Compare stated and enacted claims for one metric; gaps open contradicted unknowns."""
        with Ledger.open(_ws(workspace), write=True) as led:
            return analysis.compare_stated_vs_enacted(led, metric=metric,
                                                      entity=entity, tolerance=tolerance)

    @server.tool()
    @_safe
    def inspect_coverage(profile: str | None = None, workspace: str | None = None) -> dict:
        """Coverage by layer and by profile checklist item, computed from the ledger."""
        with Ledger.open(_ws(workspace), write=False) as led:
            return coverage.inspect_coverage(led, profile)

    @server.tool()
    @_safe
    def record_obligation(
        item: str, owner: str | None = None, case_evidence: dict[str, list[str]] | None = None,
        verifier: dict | None = None, profile: str | None = None, workspace: str | None = None,
    ) -> dict:
        """Attach owner, per-case evidence or a verifier
        ({"kind": "desk_review|reconciliation|conformance|prediction|pilot", "passed": bool,
        "evidence_ids": [...]}) to a reconstruction obligation."""
        with Ledger.open(_ws(workspace), write=True) as led:
            return _dump(coverage.record_obligation(led, item=item, owner=owner,
                                                    case_evidence=case_evidence, verifier=verifier, profile=profile))

    @server.tool()
    @_safe
    def build_obligation_ledger(profile: str | None = None, workspace: str | None = None) -> dict:
        """Status of every reconstruction obligation: ready / open / failed / unknown, with reasons."""
        with Ledger.open(_ws(workspace), write=False) as led:
            return coverage.obligation_ledger(led, profile)

    @server.tool()
    @_safe
    def render_report(language: str | None = None, profile: str | None = None,
                      out_path: str | None = None, workspace: str | None = None) -> dict:
        """Render the Markdown evidence report (ar or en). Writes to out_path if given."""
        with Ledger.open(_ws(workspace), write=False) as led:
            text = report.render_report(led, language=language, profile=profile)
            if out_path:
                Path(out_path).write_text(text, encoding="utf-8")
                return {"written": out_path}
            return {"report": text}

    # ------------------------------------------------------------ blueprint layer

    @server.tool()
    @_safe
    def show_kernel(family: str | None = None) -> Any:
        """The design kernel: the 10 building blocks every organization has (elements, design
        rules, and the traces each element leaves). family: business | public_body | nonprofit |
        industrial shows how that family builds the blocks and its specific traces."""
        from .kernel import blocks, families

        if family:
            return families()[family].model_dump()
        return [b.model_dump() for b in blocks()]

    @server.tool()
    @_safe
    def list_archetypes() -> list[dict]:
        """Typical operating models (company, ministry, organization, factory types) that seed a blueprint."""
        from .archetypes import archetypes

        return [{"id": a.id, "family": a.family, "name": a.name, "name_ar": a.name_ar, "keywords": a.keywords}
                for a in archetypes().values()]

    @server.tool()
    @_safe
    def start_blueprint(url: str | None = None, archetype: str | None = None, max_pages: int = 15,
                        workspace: str | None = None) -> dict:
        """Crawl the organization's public website (robots.txt respected) into sources and a technical
        footprint, suggest archetypes, and seed the blueprint with the chosen archetype (all
        hypotheses start at LOW confidence)."""
        from .application.blueprint import start_blueprint as start

        with Ledger.open(_ws(workspace)) as led:
            return start(led, url=url, archetype_id=archetype, max_pages=max_pages)

    @server.tool()
    @_safe
    def apply_archetype(archetype: str, workspace: str | None = None) -> dict:
        """Seed (more) archetype hypotheses into the blueprint."""
        from .archetypes import apply_archetype as apply

        with Ledger.open(_ws(workspace)) as led:
            return apply(led, archetype)

    @server.tool()
    @_safe
    def add_hypothesis(
        statement: str, component: str, basis: str, signal_evidence_ids: list[str] | None = None,
        derived_from: list[str] | None = None, assumptions: list[str] | None = None,
        range: dict | None = None, metric: str | None = None, test: str | None = None,
        test_cost: str = "medium", impact: str = "medium", archetype: str | None = None,
        workspace: str | None = None,
    ) -> dict:
        """Record an inference about how the organization works. basis: signal (cite the evidence it
        was inferred from) | archetype | calculation (derived_from + assumptions). Confidence is
        computed: archetype only = low, one source = medium, two independent sources = high.
        component: identity|customers|offer|revenue_model|acquisition|operations|team|systems|
        partners|assets|economics|moat. range: {"low","high","unit"}."""
        with Ledger.open(_ws(workspace)) as led:
            return _dump(led.add_hypothesis(
                statement=statement, component=component, basis=basis, signal_evidence_ids=signal_evidence_ids,
                derived_from=derived_from, assumptions=assumptions, range=range, metric=metric, test=test,
                test_cost=test_cost, impact=impact, archetype=archetype))

    @server.tool()
    @_safe
    def update_hypothesis(
        hypothesis_id: str, revision: int, add_signals: list[str] | None = None, status: str | None = None,
        status_evidence_ids: list[str] | None = None, test: str | None = None, impact: str | None = None,
        test_cost: str | None = None, workspace: str | None = None,
    ) -> dict:
        """Add signals or mark supported/refuted — only with evidence; support must go beyond the
        original signals."""
        with Ledger.open(_ws(workspace)) as led:
            return _dump(led.update_hypothesis(
                hypothesis_id, revision=revision, add_signals=add_signals, status=status,
                status_evidence_ids=status_evidence_ids, test=test, impact=impact, test_cost=test_cost))

    @server.tool()
    @_safe
    def promote_hypothesis(hypothesis_id: str, revision: int, workspace: str | None = None) -> dict:
        """Turn a supported hypothesis into an ordinary graded claim."""
        with Ledger.open(_ws(workspace)) as led:
            return _dump(led.promote_hypothesis(hypothesis_id, revision=revision))

    @server.tool()
    @_safe
    def grade_hypothesis(hypothesis_id: str, verdict: str, workspace: str | None = None) -> dict:
        """The owner's verdict (correct | partial | wrong), used only to calibrate confidence."""
        with Ledger.open(_ws(workspace)) as led:
            return _dump(led.grade_hypothesis(hypothesis_id, verdict))

    @server.tool()
    @_safe
    def add_design_item(component: str, kind: str, statement: str, refs: list[str], phase: str | None = None,
                        cost: dict | None = None, workspace: str | None = None) -> dict:
        """Redesign item. kind: copy | improve | cannot_copy | build_step. refs: the claim,
        hypothesis or evidence ids it rests on (required)."""
        with Ledger.open(_ws(workspace)) as led:
            return _dump(led.add_design_item(component=component, kind=kind, statement=statement, refs=refs,
                                             phase=phase, cost=cost))

    @server.tool()
    @_safe
    def add_equipment(name: str, refs: list[str], equipment_type: str | None = None, station: int | None = None,
                      count: int = 1, rate: dict | None = None, notes: str | None = None,
                      workspace: str | None = None) -> dict:
        """Equipment register entry. station = position in the routing; rate = rated rate per machine
        {"low","high","unit"} (use one unit per hour across stations to get line capacity)."""
        with Ledger.open(_ws(workspace)) as led:
            return _dump(led.add_equipment(name=name, refs=refs, equipment_type=equipment_type, station=station,
                                           count=count, rate=rate, notes=notes))

    @server.tool()
    @_safe
    def check_consistency(workspace: str | None = None) -> dict:
        """Check that the parts fit together (revenue vs volume x price, Little's law, headcount vs
        workload, stated output vs line capacity). Conflicts open unknowns."""
        from .application.consistency import check_consistency as check

        with Ledger.open(_ws(workspace)) as led:
            return check(led)

    @server.tool()
    @_safe
    def build_blueprint(workspace: str | None = None) -> dict:
        """The full blueprint: per component how it is built, what is known / inferred / unknown, the
        traces to look for; process map; organization; numbers; redesign; verification plan."""
        from .application.blueprint import build_blueprint as build

        with Ledger.open(_ws(workspace), write=False) as led:
            return build(led)

    @server.tool()
    @_safe
    def render_blueprint(language: str | None = None, md_path: str | None = None, html_path: str | None = None,
                         pdf_path: str | None = None, workspace: str | None = None) -> dict:
        """Write the blueprint as Markdown, an interactive HTML page and/or PDF (needs local Chrome)."""
        from .application.blueprint import build_blueprint as build
        from .application.blueprint_render import html_to_pdf, render_html, render_markdown

        with Ledger.open(_ws(workspace), write=False) as led:
            bp = build(led)
            lang = language or led.engagement.language
        written = {}
        if md_path:
            Path(md_path).write_text(render_markdown(bp, lang), encoding="utf-8")
            written["md"] = md_path
        if html_path or pdf_path:
            hp = Path(html_path or Path(pdf_path).with_suffix(".html"))
            hp.write_text(render_html(bp, lang), encoding="utf-8")
            written["html"] = str(hp)
            if pdf_path:
                written["pdf"] = pdf_path if html_to_pdf(hp, Path(pdf_path)) else "no local Chrome/Chromium found"
        return written or {"markdown": render_markdown(bp, lang)}

    return server


def serve() -> None:
    build_server().run()
