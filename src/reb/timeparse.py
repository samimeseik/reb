"""Lenient timestamp parsing for exports from Turkish / Arab / international tools.

Slash/dot dates are ambiguous (03/04 = 3 April or 4 March). Decide the order
once per file with `infer_dayfirst` and pass it to `parse_timestamp`; never
guess row by row.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_DMY = re.compile(
    r"^(?P<a>\d{1,4})[./-](?P<b>\d{1,2})[./-](?P<c>\d{1,4})"
    r"(?:[\sT]+(?P<h>\d{1,2}):(?P<mi>\d{2})(?::(?P<s>\d{2}))?\s*(?P<ampm>[AaPp]\.?\s?[Mm]\.?)?)?$"
)


def _normalize(value: object) -> str:
    text = str(value).strip().translate(_ARABIC_DIGITS)
    text = text.replace(" ", " ").replace(" ", " ").replace("،", ",")
    text = re.sub(r"\s*ص$", " AM", text)
    text = re.sub(r"\s*م$", " PM", text)
    text = text.replace(",", " ")
    return re.sub(r"\s+", " ", text).strip()


def infer_dayfirst(values: Iterable[object]) -> tuple[bool, bool]:
    """Return (dayfirst, ambiguous). Day-first is assumed when the data cannot tell."""
    for value in values:
        if value is None:
            continue
        m = _DMY.match(_normalize(value))
        if not m or len(m.group("a")) == 4:
            continue
        a, b = int(m.group("a")), int(m.group("b"))
        if a > 12:
            return True, False
        if b > 12:
            return False, False
    return True, True


def parse_timestamp(value: object, dayfirst: bool = True) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if value is None or str(value).strip() == "":
        return None
    text = _normalize(value)
    try:
        return datetime.fromisoformat(text).replace(tzinfo=None)
    except ValueError:
        pass
    m = _DMY.match(text)
    if not m:
        return None
    a, b, c = m.group("a"), m.group("b"), m.group("c")
    if len(a) == 4:
        year, month, day = int(a), int(b), int(c)
    elif dayfirst:
        day, month, year = int(a), int(b), int(c)
    else:
        month, day, year = int(a), int(b), int(c)
    if year < 100:
        year += 2000
    hour = int(m.group("h") or 0)
    minute = int(m.group("mi") or 0)
    second = int(m.group("s") or 0)
    ampm = (m.group("ampm") or "").replace(".", "").replace(" ", "").upper()
    if ampm == "PM" and hour < 12:
        hour += 12
    elif ampm == "AM" and hour == 12:
        hour = 0
    try:
        return datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None
