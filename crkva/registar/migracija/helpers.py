"""Pure string / date / time helpers. No DB access — easy to unit-test."""

from __future__ import annotations

import re
from datetime import date, time
from typing import Any

from registar.utils.konvertori import Konvertor

# =============================================================================
# Maiden name / surname markers
# =============================================================================

# Order is important — longer/more specific patterns first.
_MARKER_RODJENA = re.compile(r"^рођена\s+", flags=re.IGNORECASE)
_MARKER_RODJ_DOT = re.compile(r"^рођ\.\s*|^рођ\s+", flags=re.IGNORECASE)

# "р." / "р " (Cyrillic) — requires dot or whitespace to avoid eating
# names that legitimately start with Р (e.g. Радановић).
_MARKER_R_CYR = re.compile(r"^р\.\s*|^р\s+", flags=re.IGNORECASE)
_MARKER_R_LAT = re.compile(r"^r\.\s*|^r\s+", flags=re.IGNORECASE)


def clean_prezime(prezime: str | None) -> str:
    """Clean surname: remove maiden markers and fix lowercase first letter."""
    if not prezime:
        return ""

    p = prezime.strip()

    # Longer markers first to avoid leftover fragments
    for marker in (_MARKER_RODJENA, _MARKER_RODJ_DOT, _MARKER_R_CYR, _MARKER_R_LAT):
        p = marker.sub("", p)

    p = p.strip()

    # Capitalize first letter if needed
    if p and p[0].islower():
        p = p[0].upper() + p[1:]

    return p


def extract_maiden(prezime: str | None) -> tuple[str, str]:
    """Split surname field containing maiden name markers.

    Returns (married_surname, maiden_surname).

    Rules:
      - If a maiden marker is found → married_surname="", maiden_surname=extracted
      - Otherwise → married_surname=cleaned input, maiden_surname=""
      - Empty input → ("", "")
    """
    if not prezime:
        return "", ""

    raw = prezime.strip()
    if not raw:
        return "", ""

    # Try markers in order of specificity
    for marker in (_MARKER_RODJENA, _MARKER_RODJ_DOT, _MARKER_R_CYR, _MARKER_R_LAT):
        if marker.match(raw):
            maiden = marker.sub("", raw).strip()
            if maiden and maiden[0].islower():
                maiden = maiden[0].upper() + maiden[1:]
            return "", maiden

    # No marker found
    return clean_prezime(raw), ""


# =============================================================================
# Name splitting
# =============================================================================

# Matches camelCase-like glued names: "МаркоПетровић" → ("Марко", "Петровић")
_CAMEL_SPLIT = re.compile(r"^([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]*)([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)$")


def split_full_name(full_name: str | None) -> tuple[str | None, str | None]:
    """Split 'Марко Петровић' → ('Марко', 'Петровић').

    Also handles glued names like 'МаркоПетровић'.
    Returns (None, None) when splitting is not reliable.
    """
    if not full_name:
        return None, None

    cleaned = full_name.strip()
    if not cleaned:
        return None, None

    # Normal case with space
    if " " in cleaned:
        parts = cleaned.split(maxsplit=1)
        return parts[0] or None, parts[1] or None

    # Try camel-case split
    if match := _CAMEL_SPLIT.match(cleaned):
        return match.group(1), match.group(2)

    return None, None


def split_full_name_last_word(full_name: str | None) -> tuple[str, str]:
    """Split on last whitespace token.

    Example: 'Петар Никола Петровић' → ('Петар Никола', 'Петровић')
    Used in baptism records where the last word is always the surname.
    """
    if not full_name:
        return "", ""

    parts = full_name.strip().split()
    if len(parts) < 2:
        return full_name.strip(), ""

    return " ".join(parts[:-1]), parts[-1]


# =============================================================================
# Date & Time
# =============================================================================


def safe_date(y: int | None, m: int | None, d: int | None) -> date | None:
    """Return valid date or None. Rejects years before 1900."""
    y = y or 0
    m = m or 0
    d = d or 0

    if y < 1900:
        return None

    try:
        return date(y, m or 1, d or 1)
    except ValueError:
        return None


_TIME_NUMERIC = re.compile(r"^\d+([.,]\d+)?$")


def parse_time(text: str | None) -> time | None:
    """Parse sloppy time strings: '14', '14.30', '14,30', '9' → time object."""
    if not text:
        return None

    s = text.strip()
    if not s or not _TIME_NUMERIC.match(s):
        return None

    # Handle decimal/comma separator
    if "." in s:
        hh_s, mm_s = s.split(".", 1)
    elif "," in s:
        hh_s, mm_s = s.split(",", 1)
    else:
        hh_s, mm_s = s, "0"

    hh = Konvertor.int(hh_s, 12)
    mm = Konvertor.int(mm_s, 0)

    if hh == 24:
        hh = 0

    hh = max(0, min(23, hh))
    mm = max(0, min(59, mm))

    return time(hh, mm)


# =============================================================================
# Cyrillic conversion helpers
# =============================================================================


def cyr(text: str | None) -> str:
    """Convert from YUSCII/latin and strip whitespace."""
    if text is None:
        return ""
    return Konvertor.string(text).strip()


def cyr_int(value: Any, default: int = 0) -> int:
    """Safe integer conversion with fallback."""
    return Konvertor.int(value, default)
