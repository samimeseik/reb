"""WhatsApp chat exports (iOS and Android; Arabic / Turkish / English locales;
24h and 12h clocks, including Arabic ص/م).

In many small businesses the real order book is a WhatsApp group. Message
timestamps are system records; what a message *says* is testimony.
Sender names are pseudonymized before the text is stored. If the format is not
recognized, the text is NOT stored, because sender names could not be removed.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..timeparse import infer_dayfirst, parse_timestamp
from . import Extraction, FactDraft

_INVISIBLE = re.compile(r"[‎‏‪-‮﻿]")
_TS = r"\d{1,4}[./-]\d{1,2}[./-]\d{1,4}[,،]?\s\d{1,2}:\d{2}(?::\d{2})?(?:[\s ]?(?:[AaPp]\.?\s?[Mm]\.?|ص|م))?"
_IOS = re.compile(r"^\[(?P<ts>[^\]]+)\]\s*(?P<sender>[^:]{1,80}):\s(?P<body>.*)$")
_ANDROID = re.compile(rf"^(?P<ts>{_TS})\s[-–]\s(?P<sender>[^:]{{1,80}}):\s(?P<body>.*)$")


@dataclass
class Message:
    line: int
    timestamp: datetime
    sender: str
    body: str


def _matches(text: str) -> list[tuple[int, re.Match[str] | None, str]]:
    out: list[tuple[int, re.Match[str] | None, str]] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = _INVISIBLE.sub("", raw).strip()
        if line:
            out.append((number, _IOS.match(line) or _ANDROID.match(line), line))
    return out


def looks_like_chat(text: str) -> bool:
    head = [m for _, m, _ in _matches("\n".join(text.splitlines()[:30]))]
    return sum(1 for m in head if m) >= 3


def parse_text(text: str) -> list[Message]:
    rows = _matches(text)
    dayfirst, _ = infer_dayfirst(m.group("ts").split()[0].rstrip(",،") for _, m, _ in rows if m)
    messages: list[Message] = []
    for number, match, line in rows:
        ts = parse_timestamp(match.group("ts"), dayfirst=dayfirst) if match else None
        if match and ts:
            messages.append(Message(number, ts, match.group("sender").strip(), match.group("body").strip()))
        elif messages:
            messages[-1].body += "\n" + line
    return messages


def extract(path: Path) -> Extraction:
    text = path.read_text(encoding="utf-8", errors="replace")
    messages = parse_text(text)
    senders = Counter(m.sender for m in messages)
    _, ambiguous = infer_dayfirst(
        m.group("ts").split()[0].rstrip(",،") for _, m, _ in _matches(text) if m
    )
    limitations = [
        "A chat export covers one chat only; deleted messages, calls and other chats are absent.",
        "Message timestamps are records; message content is testimony.",
    ]
    if ambiguous:
        limitations.append("Date order (day/month) could not be determined from the data; day-first was assumed.")
    if not messages:
        limitations.append(
            "No messages recognized: unsupported export format. Text was not stored because "
            "sender names could not be pseudonymized."
        )
        return Extraction(provider="whatsapp", text=None, limitations=limitations)
    start, end = messages[0].timestamp, messages[-1].timestamp
    facts = [
        FactDraft(
            fact=(
                f"Chat export with {len(messages)} messages from {len(senders)} participants "
                f"between {start.date()} and {end.date()}."
            ),
            operation="inventory_chat",
            normalized={
                "messages": len(messages),
                "participants": len(senders),
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            layer="operations",
            limitations=limitations,
        )
    ]
    return Extraction(provider="whatsapp", text=text, facts=facts, names=list(senders), limitations=limitations)
