"""Guardrails enforced by the engine itself, not left to the agent's judgement.

1. Mode policy: PUBLIC engagements cannot ingest private sources.
2. Consent: interviews, recordings and chat exports need a legal basis.
3. Vocabulary: rendered findings speak in evidence grades, never in warranties.
4. Pseudonymization: personal identifiers are replaced before text is stored.
"""

from __future__ import annotations

import hashlib
import re

from .errors import RebError
from .models import Authority, Custody, Engagement, Mode, Source, SourceKind

PUBLIC_ALLOWED_KINDS = {
    SourceKind.PUBLIC_RECORD,
    SourceKind.PUBLIC_SIGNAL,
    SourceKind.DOCUMENT,
    SourceKind.IMAGE,
    SourceKind.OBSERVATION,  # what any member of the public can see
    SourceKind.FINANCIAL_STATEMENT,  # published annual reports / filed accounts
    SourceKind.SPREADSHEET,  # open-data tables
}

CONSENT_REQUIRED_KINDS = {SourceKind.INTERVIEW, SourceKind.CHAT_EXPORT, SourceKind.OBSERVATION}

# The strongest authority a source of each kind can carry. Weaker is always allowed
# (a chat message's *content* is testimony even though its timestamp is a record).
_RECORD_KINDS = {
    SourceKind.SPREADSHEET,
    SourceKind.SYSTEM_EXPORT,
    SourceKind.EINVOICE,
    SourceKind.EVENT_LOG,
    SourceKind.FINANCIAL_STATEMENT,
    SourceKind.CHAT_EXPORT,
}
_AUTHORITY_ORDER = [
    Authority.SYSTEM_RECORD,
    Authority.DIRECT_OBSERVATION,
    Authority.GOVERNING_DOCUMENT,
    Authority.PUBLIC_RECORD,
    Authority.TESTIMONY,
    Authority.PUBLIC_SIGNAL,
    Authority.ANALYST_INFERENCE,
]

# Custody "captured_live" means the analyst captured it, or watched the owner pull
# it from a system on their own device. A typed document cannot be captured live.
LIVE_CAPTURE_KINDS = _RECORD_KINDS | {SourceKind.OBSERVATION, SourceKind.IMAGE, SourceKind.INTERVIEW}


def max_authority(source: Source) -> Authority:
    kind = source.kind
    if kind in _RECORD_KINDS:
        return Authority.SYSTEM_RECORD
    if kind == SourceKind.OBSERVATION:
        return Authority.DIRECT_OBSERVATION
    if kind == SourceKind.IMAGE:
        return Authority.DIRECT_OBSERVATION if source.custody == Custody.CAPTURED_LIVE else Authority.GOVERNING_DOCUMENT
    if kind == SourceKind.INTERVIEW:
        return Authority.TESTIMONY
    if kind == SourceKind.PUBLIC_RECORD:
        return Authority.PUBLIC_RECORD
    if kind == SourceKind.PUBLIC_SIGNAL:
        return Authority.PUBLIC_SIGNAL
    return Authority.GOVERNING_DOCUMENT  # document, other


def check_authority(source: Source, authority: Authority) -> None:
    ceiling = max_authority(source)
    if _AUTHORITY_ORDER.index(authority) < _AUTHORITY_ORDER.index(ceiling):
        raise RebError(
            "authority_mismatch",
            f"A {source.kind.value} source can carry at most '{ceiling.value}' authority, not "
            f"'{authority.value}'. Corroborate with records or observation instead of upgrading it.",
        )


def _fold(value: str) -> str:
    return re.sub(r"[\s._-]+", "", value).casefold()


def _url_host(value: str | None) -> str | None:
    match = re.match(r"^[a-z][a-z0-9+.-]*://([^/:?#\s]+)", (value or "").strip(), re.IGNORECASE)
    return match.group(1).casefold().removeprefix("www.") if match else None


def is_subject_party(engagement: Engagement, source: Source) -> bool:
    """True when the source was produced or published by the subject itself:
    its origin or controller is the subject's name or a declared alias, or its URL
    is on one of the subject's declared domains."""
    names = {_fold(n) for n in [engagement.subject, *engagement.aliases] if n}
    if {_fold(source.origin_party), _fold(source.controller)} & names:
        return True
    host = _url_host(source.legal_basis)
    domains = {a.casefold().removeprefix("www.") for a in engagement.aliases if "." in a and " " not in a}
    return bool(host) and any(host == d or host.endswith("." + d) for d in domains)


def normalize_controller(engagement: Engagement, source: Source) -> None:
    """The organization's owner, staff, documents, systems, website and press releases
    share ONE controller, in every mode. Only third parties, observers and public sources
    published by others can be independent of it."""
    subject = f"subject:{engagement.subject}"
    if is_subject_party(engagement, source):
        source.controller = subject
        return
    if engagement.mode == Mode.PUBLIC:
        return
    if source.custody in (Custody.SUBJECT_HELD,) or (
        source.kind == SourceKind.INTERVIEW and source.custody != Custody.THIRD_PARTY
    ):
        source.controller = subject


_URL_RE = re.compile(r"^https?://[^\s/?#]+", re.IGNORECASE)
_REGISTRY_RE = re.compile(r"^(?=.*[^\W\d_])(?=.*\d)\S.{2,}$")


def is_public_reference(value: str | None) -> bool:
    """A URL, or a registry reference that names the registry and carries a number."""
    value = (value or "").strip()
    return bool(_URL_RE.match(value) or _REGISTRY_RE.match(value))


# A declared kind may refine the detected one within the same family (a .md page is a
# public_signal, a .csv is an event_log). Crossing families (a spreadsheet declared a
# document) changes which rules apply, so it needs a stated reason.
KIND_FAMILIES: dict[SourceKind, set[SourceKind]] = {
    SourceKind.DOCUMENT: {SourceKind.DOCUMENT, SourceKind.PUBLIC_SIGNAL, SourceKind.PUBLIC_RECORD,
                          SourceKind.FINANCIAL_STATEMENT, SourceKind.INTERVIEW, SourceKind.OBSERVATION},
    SourceKind.SPREADSHEET: {SourceKind.SPREADSHEET, SourceKind.SYSTEM_EXPORT, SourceKind.EVENT_LOG,
                             SourceKind.FINANCIAL_STATEMENT, SourceKind.PUBLIC_RECORD},
    SourceKind.EINVOICE: {SourceKind.EINVOICE, SourceKind.SYSTEM_EXPORT},
    SourceKind.IMAGE: {SourceKind.IMAGE, SourceKind.DOCUMENT, SourceKind.FINANCIAL_STATEMENT,
                       SourceKind.PUBLIC_RECORD, SourceKind.PUBLIC_SIGNAL, SourceKind.OBSERVATION},
    SourceKind.INTERVIEW: {SourceKind.INTERVIEW},
    SourceKind.CHAT_EXPORT: {SourceKind.CHAT_EXPORT},
}


def check_kind_override(detected: SourceKind, declared: SourceKind, reason: str | None) -> str | None:
    """Returns the note to keep on the source, or raises when a cross-family override has no reason."""
    family = KIND_FAMILIES.get(detected)
    # Declaring a kind that needs consent only adds protection, so it needs no reason.
    if family is None or declared in family or declared in CONSENT_REQUIRED_KINDS:
        return None
    if not (reason or "").strip():
        raise RebError(
            "kind_override_reason_required",
            f"The file looks like a {detected.value}, not a {declared.value}. Ingest it as "
            f"{sorted(k.value for k in family)}, or say why in kind_reason (it is kept and reported).",
        )
    check_vocabulary(reason)
    return f"kind override: detected {detected.value}, declared {declared.value}: {reason.strip()}"


def check_source_admissible(engagement: Engagement, source: Source, known_sources: set[str] | None = None) -> None:
    if engagement.mode == Mode.PUBLIC:
        if source.kind not in PUBLIC_ALLOWED_KINDS or source.custody != Custody.PUBLIC:
            raise RebError(
                "mode_violation",
                f"Engagement mode is 'public': only publicly available sources are admissible "
                f"(got kind={source.kind.value}, custody={source.custody.value}). "
                "Internal documents, exports, chats and interviews need mode 'self' or 'engaged'.",
            )
    if source.kind in CONSENT_REQUIRED_KINDS and source.custody != Custody.PUBLIC and not source.legal_basis:
        raise RebError(
            "consent_required",
            f"Sources of kind '{source.kind.value}' record other people's words or work. "
            "Record the consent, staff-notice or mandate reference in legal_basis first.",
        )
    if source.custody == Custody.PUBLIC and not is_public_reference(source.legal_basis):
        raise RebError(
            "public_reference_required",
            "Public sources need their URL (https://…) or a registry reference with its number "
            f"(e.g. 'MERSIS 0123456789') in legal_basis; got {source.legal_basis!r}.",
        )
    if source.custody == Custody.CAPTURED_LIVE and source.kind not in LIVE_CAPTURE_KINDS:
        raise RebError(
            "custody_mismatch",
            f"A {source.kind.value} cannot be 'captured_live'. Use captured_live for exports pulled live, "
            "photos you took, observations and interviews; documents handed over are 'subject_held'.",
        )
    if source.custody == Custody.ISSUER_VERIFIABLE:
        missing = [v for v in source.verification_ids if v not in (known_sources or set())]
        if not source.verification_ids or missing:
            raise RebError(
                "verification_required",
                "Custody 'issuer_verifiable' needs verification_ids: ingest the issuer check itself "
                "(e.g. a screenshot of the e-invoice UUID lookup) as a source first and cite it.",
            )
    if source.custody == Custody.THIRD_PARTY and source.controller.strip().lower() == source.origin_party.strip().lower() \
            and not source.controller_explicit:
        raise RebError(
            "controller_required",
            "Third-party sources need an explicit controller (which organization controls the content).",
        )
    if engagement.mode != Mode.PUBLIC and not engagement.authorization:
        raise RebError(
            "authorization_required",
            "Modes 'self' and 'engaged' need an authorization basis on the engagement "
            "(ownership, written mandate reference).",
        )


# Words that turn an evidence summary into a warranty. Findings must use grades.
BANNED_TERMS = [
    r"\bverified\b",
    r"\bproven\b",
    r"\bguarantee[sd]?\b",
    r"\bcertified\b",
    r"\b100\s?%\s?(?:accurate|sure|certain)\b",
    r"مضمون",
    r"موثّق",
    r"موثق",
    r"مُثبت",
    r"مثبت",
    r"مؤكد\s+تماما",
    r"سليمة\s+تماما",
    r"\bgaranti(?:li)?\b",
    r"\bkesinlikle\b",
]
_BANNED_RE = re.compile("|".join(BANNED_TERMS), re.IGNORECASE)


# Quoted words are reported speech ('the site says "no guarantees"'), not a warranty
# made by the analyst, so text inside quotation marks is not checked.
_QUOTED_RE = re.compile(r'"[^"]*"|“[^”]*”|«[^»]*»|„[^“”]*[“”]')


def find_banned_terms(text: str) -> list[str]:
    unquoted = _QUOTED_RE.sub(" ", text)
    return sorted({m.group(0) for m in _BANNED_RE.finditer(unquoted)})


def check_vocabulary(text: str) -> None:
    found = find_banned_terms(text)
    if found:
        raise RebError(
            "banned_vocabulary",
            f"Statement uses warranty language {found}. State what the evidence shows and let "
            "the grade carry the confidence (e.g. 'e-invoices for 12 months show…').",
        )


# --- pseudonymization -------------------------------------------------------

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,4})?\b")),
    # international (+CC …) or Turkish/Gulf mobile (05xx xxx xx xx); kept strict so
    # dates like 16.10.2026 09:15 and amounts like 12.500.000 are not touched
    ("PHONE", re.compile(r"(?<![\w+])\+\d{1,3}[\s-]?\d{2,4}[\s-]?\d{3}[\s-]?\d{2,4}(?:[\s-]?\d{2})?(?!\w)")),
    ("PHONE", re.compile(r"(?<![\w.,/])0?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\w)(?![.,/]\d)")),
    ("NATIONAL_ID", re.compile(r"\b[1-9]\d{10}\b")),  # e.g. Turkish TCKN (11 digits)
]


# Common given names (Turkish, Arabic, English). A capitalized word after one of these is
# taken as a surname, so "Ahmet Yilmaz" in a memo is pseudonymized like a chat sender.
# Heuristic: it finds most names in business documents, not all of them.
GIVEN_NAMES = {
    # Turkish
    "Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin", "Hasan", "İbrahim", "Ibrahim", "İsmail", "Ismail",
    "Osman", "Yusuf", "Murat", "Ömer", "Omer", "Ramazan", "Halil", "Süleyman", "Suleyman", "Abdullah",
    "Mahmut", "Recep", "Salih", "Fatih", "Kemal", "Emre", "Burak", "Cem", "Serkan", "Hakan", "Volkan",
    "Onur", "Kerem", "Selim", "Tolga", "Uğur", "Ugur", "Erkan", "Orhan", "Yasin", "Furkan", "Enes",
    "Fatma", "Ayşe", "Ayse", "Emine", "Hatice", "Zeynep", "Elif", "Meryem", "Şerife", "Zehra",
    "Hanife", "Merve", "Esra", "Özlem", "Ozlem", "Yasemin", "Selin", "Ebru", "Derya", "Aylin", "Ece",
    "Büşra", "Busra", "Gamze", "Tuğba", "Tugba", "Sibel", "Hülya", "Hulya", "Nur", "Seda",
    # Arabic (transliterated)
    "Mohammed", "Muhammad", "Mohamed", "Mohammad", "Ahmed", "Ahmad", "Khalid", "Khaled", "Omar", "Umar",
    "Abdulrahman", "Abdelrahman", "Hassan", "Hussein", "Hussain", "Youssef", "Yousef", "Yusef",
    "Saeed", "Said", "Sami", "Faisal", "Fahad", "Fahd", "Nasser", "Hamad", "Majid", "Tariq", "Tarek",
    "Waleed", "Walid", "Karim", "Kareem", "Mahmoud", "Mustafa", "Mostafa", "Ziad", "Ziyad", "Bilal",
    "Fatima", "Fatimah", "Aisha", "Aysha", "Mariam", "Maryam", "Noura", "Nora", "Sara", "Sarah",
    "Huda", "Layla", "Leila", "Reem", "Rim", "Hind", "Amal", "Nadia", "Salma", "Rania", "Dina",
    # English
    "John", "James", "Michael", "David", "Robert", "William", "Richard", "Thomas", "Mark", "Paul",
    "Peter", "George", "Daniel", "Andrew", "Steven", "Mary", "Anna", "Emma", "Laura", "Linda",
    "Susan", "Elizabeth", "Jennifer", "Maria", "Jessica", "Karen",
    # Arabic script
    "محمد", "أحمد", "احمد", "علي", "حسن", "حسين", "خالد", "عمر", "عبدالله", "إبراهيم", "ابراهيم",
    "يوسف", "سامي", "فيصل", "ناصر", "طارق", "وليد", "كريم", "محمود", "مصطفى", "فاطمة", "عائشة",
    "مريم", "سارة", "نورة", "هدى", "ليلى", "ريم", "هند", "أمل", "نادية", "سلمى",
}
_HONORIFIC = r"(?:Mr|Mrs|Ms|Dr|Prof|Sn|Sayın|Bay|Bayan)\.?"
_CAP = r"[A-ZÇĞİÖŞÜ][a-zçğıöşüA-ZÇĞİÖŞÜ'’-]+"
_ARABIC_WORD = r"[\u0621-\u064A]{2,}"
_ARABIC_HONORIFIC = r"(?:السيد|السيدة|الأستاذ|الأستاذة|الدكتور|الدكتورة|المهندس|المهندسة|الحاج)"


def detect_person_names(text: str | None) -> list[str]:
    """Person names in free text: a common given name followed by one or two capitalized
    words (Latin) or one word (Arabic script); a capitalized name after an honorific
    (Mr, Dr, Sayın …) or before Bey/Hanım; an Arabic name after السيد/الأستاذ/الدكتور …"""
    if not text:
        return []
    found: list[str] = []
    for m in re.finditer(rf"(?<![\w])({_CAP})((?:\s+{_CAP}){{1,2}})(?![\w])", text):
        if m.group(1) in GIVEN_NAMES:
            found.append(m.group(0).strip())
    for m in re.finditer(rf"(?<![\w]){_HONORIFIC}\s+({_CAP}(?:\s+{_CAP})?)", text):
        found.append(m.group(1))
    for m in re.finditer(rf"(?<![\w])({_CAP}(?:\s+{_CAP})?)\s+(?:Bey|Hanım|Hanim)(?![\w])", text):
        found.append(m.group(1))
    for m in re.finditer(rf"(?<![\u0621-\u064A])({_ARABIC_WORD})\s+({_ARABIC_WORD})", text):
        if m.group(1) in GIVEN_NAMES:
            found.append(m.group(0))
    for m in re.finditer(rf"{_ARABIC_HONORIFIC}\s+({_ARABIC_WORD}(?:\s+{_ARABIC_WORD})?)", text):
        found.append(m.group(1))
    return list(dict.fromkeys(found))


class Pseudonymizer:
    """Replaces identifiers with stable tokens. This is pseudonymization, not anonymization:
    the organization's originals and the local map still identify people.

    Tokens are salted per engagement, so a token in a shared report cannot be matched to
    a guessed name without the workspace. Only person names are kept in the map (they are
    needed to find the same person in later sources); identifiers found by pattern
    (e-mail, phone, IBAN, national id) are re-derived from the salt and never written down."""

    PERSISTED_KINDS = ("PERSON",)

    def __init__(self, mapping: dict[str, str] | None = None, salt: str = ""):
        self.mapping: dict[str, str] = mapping or {}
        self.salt = salt

    def token(self, kind: str, value: str) -> str:
        key = f"{kind}:{value.strip()}"
        if key not in self.mapping:
            digest = hashlib.sha256((self.salt + key).encode()).hexdigest()[:6]
            self.mapping[key] = f"[{kind}-{digest}]"
        return self.mapping[key]

    def persisted(self) -> dict[str, str]:
        return {k: v for k, v in self.mapping.items() if k.split(":", 1)[0] in self.PERSISTED_KINDS}

    def person(self, name: str, role: str | None = None) -> str:
        tok = self.token("PERSON", name)
        return f"{role} {tok}" if role else tok

    def known_names(self) -> set[str]:
        return {k.split(":", 1)[1] for k in self.mapping if k.startswith("PERSON:")}

    def scrub(self, text: str, names: list[str] | None = None) -> str:
        """Replace every person known to this engagement (from any source) plus
        `names`, on word boundaries, then identifier patterns."""
        for name in sorted(self.known_names() | set(names or []), key=len, reverse=True):
            if name.strip():
                token = self.person(name)
                text = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", lambda _m, t=token: t, text)
        for kind, pattern in _PATTERNS:
            text = pattern.sub(lambda m, k=kind: self.token(k, m.group(0)), text)
        return text
