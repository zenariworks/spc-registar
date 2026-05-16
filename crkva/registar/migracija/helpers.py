"""Pure string / date / time helpers. No DB access — easy to unit-test."""

from __future__ import annotations

import re
from datetime import date, time

from registar.management.commands.convert_utils import Konvertor

# --- Презиме (surname) ---

# Maiden-name marker: "р." / "р " / "Р." / "Р " / "r." / "r " / "R." / "R "
# + standalone "рођена " / "Рођена ".
#
# The marker REQUIRES either a period OR whitespace after the leading
# р/r — without that requirement the regex eats the first letter of any
# name starting with Р/R (e.g. "Радановић" → "адановић"). That was the
# original bug.
_MARKER_R_CYR = re.compile(r"^р\.\s*|^р\s+", flags=re.IGNORECASE)
_MARKER_R_LAT = re.compile(r"^r\.\s*|^r\s+", flags=re.IGNORECASE)
_MARKER_RODJENA = re.compile(r"^рођена\s+", flags=re.IGNORECASE)


def clean_prezime(prezime: str | None) -> str:
    """Strip maiden-name markers and capitalise a sloppy lowercase first letter."""
    if not prezime:
        return prezime or ""
    p = _MARKER_R_CYR.sub("", prezime).strip()
    p = _MARKER_R_LAT.sub("", p).strip()
    p = _MARKER_RODJENA.sub("", p).strip()
    if p and p[0].islower():
        p = p[0].upper() + p[1:]
    return p


# --- Раздвајање имена и презимена ---

_CAMEL_SPLIT = re.compile(r"^([А-ЯЂЈЉЊЋЏа-яђјљњћџ]+?)([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)$")


def split_full_name(full_name: str | None) -> tuple[str | None, str | None]:
    """Split 'Марко Петровић' → ('Марко', 'Петровић').

    Also handles run-together names like 'МаркоПетровић' by splitting at
    the inner uppercase boundary. Returns (None, None) if the name can't
    be confidently split.
    """
    if not full_name:
        return None, None
    full_name = full_name.strip()
    if not full_name:
        return None, None
    if " " in full_name:
        first, last = full_name.split(maxsplit=1)
        return first or None, last or None
    if m := _CAMEL_SPLIT.match(full_name):
        return m.group(1), m.group(2)
    return None, None


def split_full_name_last_word(full_name: str | None) -> tuple[str, str]:
    """Split, keeping the last whitespace-delimited token as prezime.

    Used by krstenje where 'Петар Никола Петровић' should give
    ime='Петар Никола', prezime='Петровић'.
    """
    if not full_name:
        return "", ""
    parts = full_name.strip().split()
    if len(parts) < 2:
        return full_name.strip(), ""
    return " ".join(parts[:-1]), parts[-1]


# --- Датум / Време ---


def safe_date(y: int | None, m: int | None, d: int | None) -> date | None:
    """Return a valid date or None. Rejects pre-1900 years."""
    y = y or 0
    m = m or 0
    d = d or 0
    if y < 1900:
        return None
    try:
        return date(y, m or 1, d or 1)
    except ValueError:
        return None


_TIME_NUM = re.compile(r"^\d+([.,]\d+)?$")


def parse_time(text: str | None) -> time | None:
    """Parse a sloppy time string ('14', '14.30', '14,30') into a `time`."""
    if text is None:
        return None
    s = text.strip()
    if not s or not _TIME_NUM.match(s):
        return None
    sep = "." if "." in s else ("," if "," in s else None)
    if sep:
        hh_s, mm_s = s.split(sep, 1)
        hh = Konvertor.int(hh_s, 12)
        mm = Konvertor.int(mm_s, 0)
    else:
        hh = Konvertor.int(s, 12)
        mm = 0
    if hh == 24:
        hh = 0
    hh = max(0, min(23, hh))
    mm = max(0, min(59, mm))
    return time(hh, mm)


# --- Текст из YUSCII латинице ---


def cyr(text: str | None) -> str:
    """Convenience: Konvertor.string + strip."""
    if text is None:
        return ""
    return Konvertor.string(text).strip()


def cyr_int(value, default: int = 0) -> int:
    return Konvertor.int(value, default)
