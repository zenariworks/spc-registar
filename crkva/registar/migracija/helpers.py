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
_MARKERI_PREZIMENA = (
    _MARKER_RODJENA,
    _MARKER_RODJ_DOT,
    _MARKER_R_CYR,
    _MARKER_R_LAT,
)


def ukloni_marker(tekst: str) -> str:
    for marker in _MARKERI_PREZIMENA:
        tekst = marker.sub("", tekst)
    return tekst.strip()


def veliko_prvo_slovo(tekst: str) -> str:
    return tekst[:1].upper() + tekst[1:]


def ocisti_prezime(prezime: str | None) -> str:
    if not prezime:
        return ""
    return veliko_prvo_slovo(ukloni_marker(prezime.strip()))


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

    for marker in _MARKERI_PREZIMENA:
        if marker.match(raw):
            return "", veliko_prvo_slovo(marker.sub("", raw).strip())

    return ocisti_prezime(raw), ""


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


def split_full_name_last_word(puno_ime: str | None) -> tuple[str, str]:
    """Split on last whitespace token.

    Example: 'Петар Никола Петровић' → ('Петар Никола', 'Петровић')
    Used in baptism records where the last word is always the surname.
    """
    if not puno_ime:
        return "", ""

    parts = puno_ime.strip().split()
    if len(parts) < 2:
        return puno_ime.strip(), ""

    return " ".join(parts[:-1]), parts[-1]


# =============================================================================
# Date & Time
# =============================================================================


def safe_date(yyyy: int | None, mm: int | None, dd: int | None) -> date | None:
    """Return valid date or None. Rejects years before 1900."""
    yyyy = yyyy or 0
    mm = mm or 0
    dd = dd or 0

    if yyyy < 1900:
        return None

    try:
        return date(yyyy, mm or 1, dd or 1)
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

    sati = Konvertor.int(hh_s, 12)
    minuti = Konvertor.int(mm_s, 0)

    sati = 0 if sati == 24 else min(max(sati, 0), 23)
    minuti = max(0, min(59, minuti))

    return time(sati, minuti)


# =============================================================================
# Cyrillic conversion helpers
# =============================================================================


def cirilica(tekst: str | None) -> str:
    """Convert from YUSCII/latin and strip whitespace."""
    if tekst is None:
        return ""
    return Konvertor.string(tekst).strip()


def cirilica_int(vrednost: Any, podrazumevano: int = 0) -> int:
    """Safe integer conversion with fallback."""
    return Konvertor.int(vrednost, podrazumevano)
