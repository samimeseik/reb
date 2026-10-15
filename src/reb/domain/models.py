"""Core records. Ported in spirit from REA's Evidence / ResidualUnknown /
reconstruction-obligation model, re-targeted from binaries to organizations."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Mode(str, Enum):
    """How the analyst is authorized to look at the organization."""

    SELF = "self"  # you own or run it
    ENGAGED = "engaged"  # written mandate from the organization
    PUBLIC = "public"  # public sources only


class Layer(str, Enum):
    STRATEGY = "strategy"
    REVENUE = "revenue"  # revenue model & pricing
    CUSTOMER = "customer"  # customer journey
    OPERATIONS = "operations"  # processes
    EQUIPMENT = "equipment"  # machines & production lines
    SYSTEMS = "systems"  # IT systems & data
    PEOPLE = "people"  # org, roles, hiring, pay
    SUPPLY = "supply"  # suppliers & supply chain
    FINANCE = "finance"  # cost structure & cash
    REGULATION = "regulation"  # licences, permits, legal status
    CULTURE = "culture"  # culture & tacit knowledge


class SourceKind(str, Enum):
    DOCUMENT = "document"  # SOP, policy, contract, manual (text/PDF)
    IMAGE = "image"  # photo, scan, nameplate
    SPREADSHEET = "spreadsheet"  # CSV / XLSX
    SYSTEM_EXPORT = "system_export"  # ERP / POS / CRM / ATS export
    EINVOICE = "einvoice"  # e-invoice XML (e.g. UBL-TR e-Fatura)
    CHAT_EXPORT = "chat_export"  # WhatsApp / Telegram export
    INTERVIEW = "interview"  # transcript or audio
    OBSERVATION = "observation"  # structured site-walk / time-study note
    EVENT_LOG = "event_log"  # case / activity / timestamp table
    FINANCIAL_STATEMENT = "financial_statement"
    PUBLIC_RECORD = "public_record"  # registry, gazette, court listing
    PUBLIC_SIGNAL = "public_signal"  # website, job ads, reviews
    OTHER = "other"


class Custody(str, Enum):
    """Who held the source when it reached the analyst. Caps the grade."""

    SUBJECT_HELD = "subject_held"  # handed over by the organization itself
    ISSUER_VERIFIABLE = "issuer_verifiable"  # checked against the issuing body
    THIRD_PARTY = "third_party"  # from a customer, supplier, bank, registry
    CAPTURED_LIVE = "captured_live"  # captured by the analyst in person
    PUBLIC = "public"  # publicly available


class Authority(str, Enum):
    """What kind of knowledge the evidence represents (strongest first)."""

    SYSTEM_RECORD = "system_record"
    DIRECT_OBSERVATION = "direct_observation"
    GOVERNING_DOCUMENT = "governing_document"
    PUBLIC_RECORD = "public_record"
    TESTIMONY = "testimony"
    PUBLIC_SIGNAL = "public_signal"
    ANALYST_INFERENCE = "analyst_inference"


class Confidence(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    INFERRED = "inferred"


class Grade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class Sensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PERSONAL = "personal"
    SPECIAL = "special"  # health, religion, union, criminal… (KVKK/GDPR special)


class ClaimKind(str, Enum):
    STATED = "stated"  # what documents / people say
    ENACTED = "enacted"  # what records / observation show
    NEUTRAL = "neutral"


class ClaimStatus(str, Enum):
    CONJECTURE = "conjecture"  # no evidence — must be shown as such
    SINGLE_SOURCE = "single_source"
    TRIANGULATED = "triangulated"
    CONTRADICTED = "contradicted"


class Replicability(str, Enum):
    CODIFIABLE = "codifiable"
    NEEDS_CAPABILITY = "needs_capability"
    NEEDS_ASSET = "needs_asset"
    NON_TRANSFERABLE = "non_transferable"
    UNASSESSED = "unassessed"


class UnknownStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    BLOCKED = "blocked"
    CONTRADICTED = "contradicted"
    RESOLVED = "resolved"


class ObligationStatus(str, Enum):
    READY = "ready"
    OPEN = "open"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ObservationContext(BaseModel):
    site: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    shift: str | None = None
    note: str | None = None


class Engagement(BaseModel):
    id: str
    name: str
    subject: str  # organization name or pseudonym
    mode: Mode
    authorization: str | None = None  # mandate / ownership basis; required unless public
    profile: str | None = None
    analyst: str | None = None
    language: str = "ar"
    created_at: str = Field(default_factory=utc_now)
    retention_until: date | None = None


class Source(BaseModel):
    id: str
    sha256: str
    kind: SourceKind
    custody: Custody
    title: str
    path: str | None = None  # where the original lives; never copied by REB
    origin_party: str  # who produced it (role/org, not a person's name)
    controller: str  # who controls its content — drives independence
    controller_explicit: bool = False
    upstream_ids: list[str] = Field(default_factory=list)  # sources it was derived from
    verification_ids: list[str] = Field(default_factory=list)  # issuer checks backing issuer_verifiable
    legal_basis: str | None = None  # consent id, mandate id or public URL
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    language: str | None = None
    context: ObservationContext = Field(default_factory=ObservationContext)
    independent_channel: bool = False  # third-party contact found without the subject's help
    captured_at: str = Field(default_factory=utc_now)
    text_path: str | None = None  # cached extracted text (inside the workspace)
    notes: str | None = None


class Evidence(BaseModel):
    id: str
    source_id: str
    provider: str
    operation: str
    fact: str
    location: str | None = None  # page/line/timestamp/cell
    quote: str | None = None  # verbatim span, verified against the source text
    entity: str | None = None
    layer: Layer | None = None
    authority: Authority
    confidence: Confidence = Confidence.OBSERVED
    grade: Grade
    normalized: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    as_of: str | None = None
    recorded_at: str = Field(default_factory=utc_now)


class Claim(BaseModel):
    id: str
    statement: str
    layer: Layer
    entity: str | None = None
    item: str | None = None  # profile checklist item id
    kind: ClaimKind = ClaimKind.NEUTRAL
    metric: str | None = None  # for stated-vs-enacted comparison
    value: float | None = None
    unit: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    replicability: Replicability = Replicability.UNASSESSED
    industry_prior: bool = False  # relies on general knowledge, not this organization
    status: ClaimStatus = ClaimStatus.CONJECTURE
    grade: Grade | None = None
    as_of: str | None = None
    recorded_at: str = Field(default_factory=utc_now)


class Resolution(BaseModel):
    kind: str  # verified | refuted | out_of_scope
    evidence_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class Unknown(BaseModel):
    id: str
    question: str
    layer: Layer | None = None
    entity: str | None = None
    item: str | None = None
    status: UnknownStatus = UnknownStatus.OPEN
    revision: int = 1
    required_authority: Authority | None = None
    recommended_probes: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    resolution: Resolution | None = None
    updated_at: str = Field(default_factory=utc_now)


class Verifier(BaseModel):
    kind: str  # desk_review | reconciliation | conformance | prediction | pilot
    passed: bool | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class Obligation(BaseModel):
    id: str
    item: str
    layer: Layer
    statement: str
    owner: str | None = None  # accountable role in the rebuilt organization
    required_cases: list[str] = Field(default_factory=list)
    required_grade: Grade = Grade.C
    case_evidence: dict[str, list[str]] = Field(default_factory=dict)
    verifier: Verifier | None = None
    status: ObligationStatus = ObligationStatus.UNKNOWN
    reasons: list[str] = Field(default_factory=list)


class LedgerData(BaseModel):
    schema_version: int = 1
    engagement: Engagement
    sources: dict[str, Source] = Field(default_factory=dict)
    evidence: dict[str, Evidence] = Field(default_factory=dict)
    claims: dict[str, Claim] = Field(default_factory=dict)
    unknowns: dict[str, Unknown] = Field(default_factory=dict)
    obligations: dict[str, Obligation] = Field(default_factory=dict)
