"""Providers read one kind of source and return normalized facts.

Like REA's provider rule: a provider owns its parsing; consumers read the
provider's normalized facts and never re-parse the raw source.
Heavy dependencies (PDF, OCR, Excel, audio) are optional extras.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..domain.models import Authority, Custody, SourceKind


@dataclass
class FactDraft:
    fact: str
    operation: str
    location: str | None = None
    normalized: dict[str, Any] = field(default_factory=dict)
    layer: str | None = None
    entity: str | None = None
    limitations: list[str] = field(default_factory=list)


@dataclass
class Extraction:
    provider: str
    text: str | None = None
    facts: list[FactDraft] = field(default_factory=list)
    rows: list[dict[str, Any]] | None = None  # tabular payload for analyses
    names: list[str] = field(default_factory=list)  # person names to pseudonymize
    limitations: list[str] = field(default_factory=list)


EXTENSION_KINDS: dict[str, SourceKind] = {
    ".txt": SourceKind.DOCUMENT,
    ".md": SourceKind.DOCUMENT,
    ".pdf": SourceKind.DOCUMENT,
    ".docx": SourceKind.DOCUMENT,
    ".csv": SourceKind.SPREADSHEET,
    ".tsv": SourceKind.SPREADSHEET,
    ".xlsx": SourceKind.SPREADSHEET,
    ".xml": SourceKind.EINVOICE,
    ".png": SourceKind.IMAGE,
    ".jpg": SourceKind.IMAGE,
    ".jpeg": SourceKind.IMAGE,
    ".webp": SourceKind.IMAGE,
    ".mp3": SourceKind.INTERVIEW,
    ".m4a": SourceKind.INTERVIEW,
    ".wav": SourceKind.INTERVIEW,
    ".ogg": SourceKind.INTERVIEW,
    ".opus": SourceKind.INTERVIEW,
}


# Container and media formats whose bytes are never a plain-text chat. Every other
# file is sniffed, whatever its extension.
BINARY_SUFFIXES = {
    ".pdf", ".docx", ".xlsx", ".xls", ".zip", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic",
    ".mp3", ".m4a", ".wav", ".ogg", ".opus", ".mp4", ".mov",
}


def _text_head(path: Path, size: int = 8000) -> str | None:
    with path.open("rb") as fh:
        raw = fh.read(size)
    if b"\x00" in raw:
        return None
    return raw.decode("utf-8", errors="replace")


def detect_kind(path: Path) -> SourceKind:
    """Detect by content first for every text-like file, so a chat export renamed or
    re-saved as .csv/.md/.log/.json is still a chat export (it still needs a legal
    basis, and its senders are still pseudonymized)."""
    suffix = path.suffix.lower()
    if suffix not in BINARY_SUFFIXES:
        from .whatsapp import looks_like_chat

        head = _text_head(path)
        if head is not None and looks_like_chat(head):
            return SourceKind.CHAT_EXPORT
    return EXTENSION_KINDS.get(suffix, SourceKind.OTHER)


def default_authority(kind: SourceKind, custody: Custody) -> Authority:
    if kind in (
        SourceKind.SPREADSHEET,
        SourceKind.SYSTEM_EXPORT,
        SourceKind.EINVOICE,
        SourceKind.EVENT_LOG,
        SourceKind.FINANCIAL_STATEMENT,
        SourceKind.CHAT_EXPORT,  # message timestamps are records; message content is testimony
    ):
        return Authority.SYSTEM_RECORD
    if kind == SourceKind.INTERVIEW:
        return Authority.TESTIMONY
    if kind == SourceKind.OBSERVATION:
        return Authority.DIRECT_OBSERVATION
    if kind == SourceKind.IMAGE:
        return Authority.DIRECT_OBSERVATION if custody == Custody.CAPTURED_LIVE else Authority.GOVERNING_DOCUMENT
    if kind == SourceKind.PUBLIC_RECORD:
        return Authority.PUBLIC_RECORD
    if kind == SourceKind.PUBLIC_SIGNAL:
        return Authority.PUBLIC_SIGNAL
    if kind == SourceKind.DOCUMENT:
        return Authority.GOVERNING_DOCUMENT
    return Authority.ANALYST_INFERENCE


def extract(path: Path, kind: SourceKind, **options: Any) -> Extraction:
    from . import audio, documents, efatura, spreadsheet, whatsapp

    if kind == SourceKind.CHAT_EXPORT:
        return whatsapp.extract(path)
    if kind == SourceKind.EINVOICE:
        return efatura.extract(path)
    if kind in (SourceKind.SPREADSHEET, SourceKind.SYSTEM_EXPORT, SourceKind.EVENT_LOG):
        return spreadsheet.extract(path)
    if kind == SourceKind.INTERVIEW and path.suffix.lower() not in (".txt", ".md"):
        return audio.extract(path, language=options.get("language"))
    if kind == SourceKind.IMAGE:
        return documents.extract_image(path, language=options.get("language"))
    return documents.extract(path)
