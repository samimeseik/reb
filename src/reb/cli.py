"""`reb` command line. Uses the same application workflows as the MCP server."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .application import analysis, coverage, ingest, report
from pydantic import ValidationError

from .domain.errors import RebError
from .domain.ledger import Ledger
from .profiles import list_profiles


def _print(data: Any, as_json: bool) -> None:
    if as_json or not isinstance(data, str):
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        print(data)


READ_ONLY = {"read", "coverage", "ledger", "report", "export"}


def _case_pairs(values: list[str] | None) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for v in values or []:
        case, _, ids = v.partition("=")
        result[case] = [i for i in ids.split(",") if i]
    return result


def run(args: argparse.Namespace) -> Any:
    cmd = args.command
    if cmd == "profiles":
        return [{"id": p.id, "name": p.name, "name_ar": p.name_ar, "modes": [m.value for m in p.allowed_modes], "items": len(p.items)} for p in list_profiles()]
    if cmd == "init":
        if args.profile:
            from .profiles import load_profile

            prof = load_profile(args.profile)
            if args.mode not in [m.value for m in prof.allowed_modes]:
                raise RebError(
                    "mode_not_allowed",
                    f"Profile '{prof.id}' runs in modes {[m.value for m in prof.allowed_modes]}, not '{args.mode}'.",
                )
        led = Ledger.init(
            Path(args.workspace),
            name=args.name,
            subject=args.subject,
            mode=args.mode,
            authorization=args.authorization,
            profile=args.profile,
            analyst=args.analyst,
            language=args.language,
        )
        return led.engagement.model_dump(mode="json")

    with Ledger.open(Path(args.workspace), write=cmd not in READ_ONLY) as led:
        return _run_engagement(led, args)


def _run_engagement(led: Ledger, args: argparse.Namespace) -> Any:
    cmd = args.command
    if cmd == "ingest":
        return ingest.ingest_file(
            led,
            args.path,
            custody=args.custody,
            origin_party=args.origin,
            controller=args.controller,
            kind=args.kind,
            title=args.title,
            legal_basis=args.legal_basis,
            sensitivity=args.sensitivity,
            language=args.language,
            upstream_ids=args.upstream,
            verification_ids=args.verification,
            independent_channel=args.independent_channel,
            context={"site": args.site, "period_start": args.period_start, "period_end": args.period_end},
            notes=args.notes,
        )
    if cmd == "read":
        return ingest.read_source(led, args.source_id, start_line=args.start, max_lines=args.max)
    if cmd == "observe":
        facts = [json.loads(f) if f.strip().startswith("{") else {"fact": f} for f in args.fact or []]
        return ingest.record_observation(
            led, title=args.title, note=args.note, observer_role=args.role, legal_basis=args.legal_basis, site=args.site,
            when=args.when, shift=args.shift, facts=facts, public_premises=args.public_premises,
        )
    if cmd == "evidence":
        ev = led.add_evidence(
            source_id=args.source, fact=args.fact, authority=args.authority, confidence=args.confidence,
            location=args.location, quote=args.quote, entity=args.entity, layer=args.layer, as_of=args.as_of,
        )
        return ev.model_dump(mode="json")
    if cmd == "claim":
        c = led.record_claim(
            statement=args.statement, layer=args.layer, evidence_ids=args.evidence,
            contradicting_evidence_ids=args.contradicting, entity=args.entity, item=args.item,
            kind=args.kind, metric=args.metric, value=args.value, unit=args.unit,
            replicability=args.replicability, industry_prior=args.industry_prior, as_of=args.as_of,
        )
        return c.model_dump(mode="json")
    if cmd == "unknown":
        if args.unknown_cmd == "add":
            u = led.record_unknown(
                question=args.question, layer=args.layer, entity=args.entity, item=args.item,
                required_authority=args.required_authority, recommended_probes=args.probe,
                supporting_evidence_ids=args.supporting, contradicting_evidence_ids=args.contradicting,
            )
        else:
            resolution = None
            if args.resolution:
                resolution = {"kind": args.resolution, "evidence_ids": args.resolution_evidence or [], "note": args.note}
            u = led.update_unknown(
                args.unknown_id, revision=args.revision, status=args.status,
                add_supporting=args.supporting, add_contradicting=args.contradicting,
                add_probes=args.probe, resolution=resolution,
            )
        return u.model_dump(mode="json")
    if cmd == "eventlog":
        amap = json.loads(Path(args.activity_map).read_text(encoding="utf-8")) if args.activity_map else None
        result = analysis.analyze_event_log(
            led, args.source_id, case_column=args.case_column, activity_column=args.activity_column,
            time_column=args.time_column, activity_map=amap, case_pattern=args.case_pattern, entity=args.entity,
        )
        if args.mermaid:
            Path(args.mermaid).write_text(result["mermaid"] + "\n", encoding="utf-8")
        return result
    if cmd == "invoices":
        return analysis.analyze_invoices(led, args.source_ids, direction=args.direction)
    if cmd == "compare":
        return analysis.compare_stated_vs_enacted(led, metric=args.metric, entity=args.entity, tolerance=args.tolerance)
    if cmd == "coverage":
        return coverage.inspect_coverage(led, args.profile)
    if cmd == "obligation":
        verifier = None
        if args.verifier:
            verifier = {
                "kind": args.verifier,
                "passed": True if args.passed else False if args.failed else None,
                "evidence_ids": args.verifier_evidence or [],
                "note": args.note,
            }
        ob = coverage.record_obligation(
            led, item=args.item, owner=args.owner, case_evidence=_case_pairs(args.case), verifier=verifier, profile=args.profile
        )
        return ob.model_dump(mode="json")
    if cmd == "ledger":
        return coverage.obligation_ledger(led, args.profile)
    if cmd == "report":
        text = report.render_report(led, language=args.lang, profile=args.profile)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            return {"written": args.out}
        return text
    if cmd == "export":
        return json.loads(led.data.model_dump_json())
    raise RebError("unknown_command", cmd)


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-w", "--workspace", default=argparse.SUPPRESS, help="engagement workspace (default: current dir)")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="JSON output")
    p = argparse.ArgumentParser(prog="reb", description="REB: Reverse Engineer any Business — evidence-graded.", parents=[common])
    p.add_argument("--version", action="version", version=f"reb {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    _add = sub.add_parser

    def add_parser(name: str, **kwargs: Any) -> argparse.ArgumentParser:
        return _add(name, parents=[common], **kwargs)

    sub.add_parser = add_parser  # type: ignore[method-assign]

    sub.add_parser("profiles", help="list built-in profiles")

    s = sub.add_parser("init", help="open an engagement in the workspace")
    s.add_argument("--name", required=True)
    s.add_argument("--subject", required=True, help="organization name or pseudonym")
    s.add_argument("--mode", required=True, choices=["self", "engaged", "public"])
    s.add_argument("--authorization", help="ownership or written-mandate reference (required unless public)")
    s.add_argument("--profile")
    s.add_argument("--analyst")
    s.add_argument("--language", default="ar", choices=["ar", "en"])

    s = sub.add_parser("ingest", help="register a source file and extract its facts")
    s.add_argument("path")
    s.add_argument("--custody", required=True, choices=["subject_held", "issuer_verifiable", "third_party", "captured_live", "public"])
    s.add_argument("--origin", required=True, help="who produced it (role or organization, not a person's name)")
    s.add_argument("--controller", help="who controls its content (default: origin)")
    s.add_argument("--kind")
    s.add_argument("--title")
    s.add_argument("--legal-basis", help="consent id, mandate id or public URL")
    s.add_argument("--sensitivity", default="internal", choices=["public", "internal", "personal", "special"])
    s.add_argument("--language")
    s.add_argument("--upstream", action="append", help="source id this was derived from")
    s.add_argument("--verification", action="append", help="source id of the issuer check (needed for issuer_verifiable)")
    s.add_argument("--notes")
    s.add_argument("--independent-channel", action="store_true", help="third-party contact found without the subject's help")
    s.add_argument("--site")
    s.add_argument("--period-start")
    s.add_argument("--period-end")

    s = sub.add_parser("read", help="read a source's stored text with line numbers")
    s.add_argument("source_id")
    s.add_argument("--start", type=int, default=1)
    s.add_argument("--max", type=int, default=200)

    s = sub.add_parser("observe", help="record a site-walk / time-study observation")
    s.add_argument("--title", required=True)
    s.add_argument("--note", required=True)
    s.add_argument("--role", required=True, help="observer role")
    s.add_argument("--legal-basis", help="staff notice / consent reference (not needed with --public-premises)")
    s.add_argument("--site")
    s.add_argument("--when")
    s.add_argument("--shift")
    s.add_argument("--fact", action="append", help='fact text or JSON {"fact":..,"layer":..,"entity":..}')
    s.add_argument("--public-premises", action="store_true")

    s = sub.add_parser("evidence", help="record a fact from a source (quote is checked against the text)")
    s.add_argument("--source", required=True)
    s.add_argument("--fact", required=True)
    s.add_argument("--authority", required=True)
    s.add_argument("--confidence", default="observed", choices=["observed", "derived", "inferred"])
    s.add_argument("--location")
    s.add_argument("--quote")
    s.add_argument("--entity")
    s.add_argument("--layer")
    s.add_argument("--as-of")

    s = sub.add_parser("claim", help="record a claim backed by evidence")
    s.add_argument("--statement", required=True)
    s.add_argument("--layer", required=True)
    s.add_argument("--evidence", action="append")
    s.add_argument("--contradicting", action="append")
    s.add_argument("--entity")
    s.add_argument("--item")
    s.add_argument("--kind", default="neutral", choices=["stated", "enacted", "neutral"])
    s.add_argument("--metric")
    s.add_argument("--value", type=float)
    s.add_argument("--unit")
    s.add_argument("--replicability", default="unassessed", choices=["codifiable", "needs_capability", "needs_asset", "non_transferable", "unassessed"])
    s.add_argument("--industry-prior", action="store_true")
    s.add_argument("--as-of")

    s = sub.add_parser("unknown", help="record or update an unknown")
    us = s.add_subparsers(dest="unknown_cmd", required=True)
    a = us.add_parser("add")
    a.add_argument("--question", required=True)
    a.add_argument("--layer")
    a.add_argument("--entity")
    a.add_argument("--item")
    a.add_argument("--required-authority")
    a.add_argument("--probe", action="append")
    a.add_argument("--supporting", action="append")
    a.add_argument("--contradicting", action="append")
    u = us.add_parser("update")
    u.add_argument("unknown_id")
    u.add_argument("--revision", type=int, required=True)
    u.add_argument("--status", choices=["open", "investigating", "blocked", "contradicted", "resolved"])
    u.add_argument("--supporting", action="append")
    u.add_argument("--contradicting", action="append")
    u.add_argument("--probe", action="append")
    u.add_argument("--resolution", choices=["verified", "refuted", "out_of_scope"])
    u.add_argument("--resolution-evidence", action="append")
    u.add_argument("--note")

    s = sub.add_parser("eventlog", help="discover the process from an event table or chat export")
    s.add_argument("source_id")
    s.add_argument("--case-column")
    s.add_argument("--activity-column")
    s.add_argument("--time-column")
    s.add_argument("--activity-map", help='JSON file {"activity": ["keyword", ...]} (chat exports)')
    s.add_argument("--case-pattern", help="regex with one group for the case id (chat exports)")
    s.add_argument("--entity")
    s.add_argument("--mermaid", help="write the process graph as Mermaid to this file")

    s = sub.add_parser("invoices", help="revenue or spend concentration across e-invoices")
    s.add_argument("source_ids", nargs="+")
    s.add_argument("--direction", default="sales", choices=["sales", "purchases"])

    s = sub.add_parser("compare", help="stated vs enacted for one metric")
    s.add_argument("--metric", required=True)
    s.add_argument("--entity")
    s.add_argument("--tolerance", type=float, default=0.15)

    s = sub.add_parser("coverage", help="coverage by layer and profile item")
    s.add_argument("--profile")

    s = sub.add_parser("obligation", help="record owner, case evidence or verifier for an obligation")
    s.add_argument("--item", required=True)
    s.add_argument("--owner")
    s.add_argument("--case", action="append", help="case=ev_1,ev_2")
    s.add_argument("--verifier", choices=["desk_review", "reconciliation", "conformance", "prediction", "pilot"])
    g = s.add_mutually_exclusive_group()
    g.add_argument("--passed", action="store_true")
    g.add_argument("--failed", action="store_true")
    s.add_argument("--verifier-evidence", action="append")
    s.add_argument("--note")
    s.add_argument("--profile")

    s = sub.add_parser("ledger", help="reconstruction obligation ledger")
    s.add_argument("--profile")

    s = sub.add_parser("report", help="render the evidence report (Markdown)")
    s.add_argument("--lang", choices=["ar", "en"])
    s.add_argument("--profile")
    s.add_argument("--out")

    sub.add_parser("export", help="export the full ledger as JSON")

    s = sub.add_parser("mcp", help="run the MCP server (stdio)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.workspace = getattr(args, "workspace", ".")
    args.json = getattr(args, "json", False)
    if args.command == "mcp":
        from .mcp_server import serve

        serve()
        return 0
    try:
        try:
            result = run(args)
        except (ValueError, ValidationError) as exc:
            raise RebError("invalid_input", str(exc).splitlines()[0] if str(exc) else repr(exc)) from exc
        _print(result, args.json)
        return 0
    except RebError as err:
        print(json.dumps(err.to_dict(), ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
