"""Pure string / date / time helpers. No DB access — easy to unit-test."""

from __future__ import annotations

import logging
import re
from datetime import date, time
from typing import Any

from registar.utils.preslovljavanje import preslovi

logger = logging.getLogger(__name__)

# =============================================================================
# Маркери девојачког презимена
# =============================================================================

# Редослед је важан — дужи/специфичнији обрасци иду први.
_MARKER_RODJENA = re.compile(r"^рођена\s+", flags=re.IGNORECASE)
_MARKER_RODJ_DOT = re.compile(r"^рођ\.\s*|^рођ\s+", flags=re.IGNORECASE)

# „р." / „р " (ћирилица) — захтева тачку или размак да не би прогутао
# имена која легитимно почињу на Р (нпр. Радановић).
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


def izdvoj_devojacko(prezime: str | None) -> tuple[str, str]:
    """Раздваја поље презимена које садржи маркере девојачког презимена.

    Враћа (удато_презиме, девојачко_презиме).

    Правила:
      - Ако се нађе маркер девојачког → удато_презиме="", девојачко=издвојено
      - Иначе → удато_презиме=очишћен унос, девојачко=""
      - Празан унос → ("", "")
    """
    if not (tekst := (prezime or "").strip()):
        return "", ""

    if marker := next((m for m in _MARKERI_PREZIMENA if m.match(tekst)), None):
        devojacko = marker.sub("", tekst).strip()
        return "", veliko_prvo_slovo(devojacko)

    return ocisti_prezime(tekst), ""


# =============================================================================
# Name splitting
# =============================================================================

# Matches camelCase-like glued names: "МаркоПетровић" → ("Марко", "Петровић")
_CAMEL_SPLIT = re.compile(r"^([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]*)([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)$")


def rasclani_puno_ime(puno_ime: str | None) -> tuple[str | None, str | None]:
    """Split 'Марко Петровић' → ('Марко', 'Петровић').

    Also handles glued names like 'МаркоПетровић'.
    Returns (None, None) when splitting is not reliable.
    """
    if not (tekst := (puno_ime or "").strip()):
        return None, None

    if " " in tekst:
        ime, prezime = tekst.split(maxsplit=1)
        return ime, prezime

    if poklapanje := _CAMEL_SPLIT.fullmatch(tekst):
        return poklapanje.group(1), poklapanje.group(2)

    return None, None


def podeli_zadnju_rec(puno_ime: str | None) -> tuple[str, str]:
    """Split on the last whitespace-separated word.

    Example:
        "Петар Никола Петровић" -> ("Петар Никола", "Петровић")
    """
    if not (tekst := (puno_ime or "").strip()):
        return "", ""

    *ime, prezime = tekst.split()

    return (" ".join(ime), prezime) if ime else (prezime, "")


# =============================================================================
# Date & Time
# =============================================================================


def siguran_datum(
    godina: int | None, mesec: int | None, dan: int | None
) -> date | None:
    """Return a valid date or ``None``. Reject years before 1900."""
    if (godina := godina or 0) < 1900:
        return None

    try:
        return date(godina, mesec or 1, dan or 1)
    except ValueError:
        return None


_TIME_NUMERIC = re.compile(r"^\d+([.,]\d+)?$")


def u_int(vrednost: object, podrazumevano: int = 0) -> int:
    """Безбедна конверзија у int."""
    try:
        return int(vrednost)
    except (TypeError, ValueError):
        logger.warning("Неуспела конверзија у int: %r", vrednost)
        return podrazumevano


def rasclani_vreme(tekst: str | None) -> time | None:
    """Parse sloppy time strings: '14', '14.30', '14,30', '9'."""
    if not (tekst := (tekst or "").strip()) or not _TIME_NUMERIC.fullmatch(tekst):
        return None

    sati_s, *minuti_s = tekst.replace(",", ".").split(".", 1)

    sati = u_int(sati_s, 12)
    minuti = u_int(minuti_s[0] if minuti_s else "0", 0)

    sati = 0 if sati == 24 else max(0, min(sati, 23))
    minuti = max(0, min(minuti, 59))

    return time(sati, minuti)


# =============================================================================
# Cyrillic conversion helpers
# =============================================================================


def cirilica(tekst: str | None) -> str:
    """Convert from YUSCII/latin and strip whitespace."""
    if tekst is None:
        return ""
    return preslovi(tekst).strip()


def cirilica_int(vrednost: Any, podrazumevano: int = 0) -> int:
    """Safe integer conversion with fallback."""
    return u_int(vrednost, podrazumevano)
