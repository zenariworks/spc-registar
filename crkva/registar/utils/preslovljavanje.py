"""
Пресловљавање латиница ↔ ћирилица (српски) и DBF конвертори.

Садржи:
- ``preslovljavanje(tekst, u="cir"|"lat")`` — транслитерација у оба смера.
- ``get_query_variants`` — варијанте упита за претрагу (подршка за латиницу без дијакритика).
- ``Konvertor`` — помоћне методе за миграцију из legacy DBF фајлова.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from functools import lru_cache
from itertools import product
from typing import Literal

logger = logging.getLogger(__name__)

# =============================================================================
# Константе и мапе
# =============================================================================

DIGRAFI = (
    ("DŽ", "Џ"),
    ("Dž", "Џ"),
    ("dž", "џ"),
    ("NJ", "Њ"),
    ("Nj", "Њ"),
    ("nj", "њ"),
    ("LJ", "Љ"),
    ("Lj", "Љ"),
    ("lj", "љ"),
)

DIGRAFI_UNOS = DIGRAFI + (
    ("Đ", "Ђ"),
    ("đ", "ђ"),
    ("DJ", "Ђ"),
    ("Dj", "Ђ"),
    ("dj", "ђ"),
    ("Š", "Ш"),
    ("š", "ш"),
    ("Č", "Ч"),
    ("č", "ч"),
    ("Ć", "Ћ"),
    ("ć", "ћ"),
    ("Ž", "Ж"),
    ("ž", "ж"),
)

# Канонска мапа (латиница → ћирилица)
LATINICA_CIRILICA: dict[str, str] = {
    "A": "А",
    "a": "а",
    "B": "Б",
    "b": "б",
    "V": "В",
    "v": "в",
    "G": "Г",
    "g": "г",
    "D": "Д",
    "d": "д",
    "Đ": "Ђ",
    "đ": "ђ",
    "E": "Е",
    "e": "е",
    "Ž": "Ж",
    "ž": "ж",
    "Z": "З",
    "z": "з",
    "I": "И",
    "i": "и",
    "J": "Ј",
    "j": "ј",
    "K": "К",
    "k": "к",
    "L": "Л",
    "l": "л",
    "M": "М",
    "m": "м",
    "N": "Н",
    "n": "н",
    "O": "О",
    "o": "о",
    "P": "П",
    "p": "п",
    "R": "Р",
    "r": "р",
    "S": "С",
    "s": "с",
    "Š": "Ш",
    "š": "ш",
    "T": "Т",
    "t": "т",
    "U": "У",
    "u": "у",
    "F": "Ф",
    "f": "ф",
    "H": "Х",
    "h": "х",
    "C": "Ц",
    "c": "ц",
    "Č": "Ч",
    "č": "ч",
    "Ć": "Ћ",
    "ć": "ћ",
}

# Инверзна мапа (ћирилица → латиница)
CIRILICA_LATINICA: dict[str, str] = {cir: lat for lat, cir in LATINICA_CIRILICA.items()}
CIRILICA_LATINICA.update(
    {
        "Џ": "Dž",
        "џ": "dž",
        "Љ": "Lj",
        "љ": "lj",
        "Њ": "Nj",
        "њ": "nj",
    }
)

# Legacy HramSP/YUSCII подршка (само за DBF миграцију)
_HRAMSP_LEGACY = {
    "Q": "Љ",
    "q": "љ",
    "W": "Њ",
    "w": "њ",
    "[": "Ш",
    "{": "ш",
    "\\": "Ђ",
    "|": "ђ",
    "^": "Ч",
    "~": "ч",
    "]": "Ћ",
    "}": "ћ",
    "@": "Ж",
    "`": "ж",
    "X": "Џ",
    "x": "џ",
}

_HRAMSP_MAPA = LATINICA_CIRILICA | _HRAMSP_LEGACY

# =============================================================================
# Варијанте за претрагу (латиница без дијакритика)
# =============================================================================

_LATIN_AMBIGUOUS = {
    "c": ("ц", "ч", "ћ"),
    "C": ("Ц", "Ч", "Ћ"),
    "s": ("с", "ш"),
    "S": ("С", "Ш"),
    "z": ("з", "ж"),
    "Z": ("З", "Ж"),
    "d": ("д", "ђ"),
    "D": ("Д", "Ђ"),
}

_LATIN_SIMPLE_MAP = {
    lat: cir
    for lat, cir in LATINICA_CIRILICA.items()
    if lat.isascii() and lat not in _LATIN_AMBIGUOUS
}


# =============================================================================
# Помоћне функције
# =============================================================================


def _make_translator(mapping: dict[str, str]) -> dict[int, str]:
    """Креира str.translate табелу."""
    return str.maketrans(mapping)


_HRAMSP_PREVOD = _make_translator(_HRAMSP_MAPA)
_CIR_TO_LAT_PREVOD = _make_translator(CIRILICA_LATINICA)


def _preslovi(
    text: str | None,
    *,
    digrafi: tuple[tuple[str, str], ...],
    prevod: dict[int, str],
) -> str:
    """Језгро пресловљавања: прво диграфи, па појединачни карактери."""
    if not text:
        return ""

    text = text.strip()
    if not text:
        return ""

    for src, dst in digrafi:
        text = text.replace(src, dst)

    return text.translate(prevod)


@lru_cache(maxsize=512)
def preslovljavanje(text: str | None, u: Literal["cir", "lat"] = "cir") -> str:
    """Пресловљава српски текст између латинице и ћирилице."""
    if not text:
        return ""

    if u == "cir":
        return _preslovi(text, digrafi=DIGRAFI_UNOS, prevod=_HRAMSP_PREVOD)
    elif u == "lat":
        return text.translate(_CIR_TO_LAT_PREVOD)
    else:
        raise ValueError(
            f"nepoznat smer preslovljavanja: {u!r} (ocekivano 'cir'/'lat')"
        )


def _latin_to_cyrillic_variants(text: str) -> list[str]:
    """Генерише све разумне ћириличне варијанте за латиницу без дијакритика."""
    if not text:
        return [""]

    # Замени диграфе
    intermediate = text
    for src, dst in DIGRAFI_UNOS:
        intermediate = intermediate.replace(src, dst)

    # Генериши варијанте помоћу product (много читљивије од ручног loop-а)
    parts = []
    for ch in intermediate:
        if ch in _LATIN_AMBIGUOUS:
            parts.append(_LATIN_AMBIGUOUS[ch])
        elif ch in _LATIN_SIMPLE_MAP:
            parts.append((_LATIN_SIMPLE_MAP[ch],))
        else:
            parts.append((ch,))

    # Ограничимо експлозију
    variants = ["".join(combo) for combo in product(*parts)][:64]
    return variants


def get_query_variants(tekst: str) -> list[str]:
    """Враћа јединствене варијанте за претрагу (оригинал + ћирилица + латиница)."""
    if not tekst:
        return []

    variante = {tekst}
    variante.update(_latin_to_cyrillic_variants(tekst))
    variante.add(preslovljavanje(tekst, u="lat"))

    return sorted(v for v in variante if v)  # sorted за детерминистички редослед


# =============================================================================
# Konvertor — DBF миграција
# =============================================================================


class Konvertor:
    """Помоћне методе за конверзију legacy DBF података."""

    @staticmethod
    def int(vrednost: str | int | None, default: int = 0) -> int:
        """Безбедна конверзија у int."""
        if vrednost is None:
            return default
        try:
            return int(vrednost)
        except (ValueError, TypeError):
            logger.warning("Неуспела конверзија у int: %r", vrednost)
            return default

    @staticmethod
    def datum(g: int | None, m: int | None, d: int | None) -> date:
        """Креира датум, замењујући 0 вредности из DBF-ова."""
        godina = g or 1900
        mesec = m or 1
        dan = d or 1
        return date(godina, mesec, dan)

    @staticmethod
    def split_name(puno_ime: str | None) -> tuple[str | None, str | None]:
        """Раздваја име и презиме (подршка за размак и CamelCase ћирилицу)."""
        if not puno_ime or not (puno_ime := puno_ime.strip()):
            return None, None

        # 1. Обичан размак
        if " " in puno_ime:
            first, *rest = puno_ime.split()
            return first, " ".join(rest)

        # 2. CamelCase (нпр. СлавицаЋуковић)
        if match := re.match(
            r"^([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]*?)([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]*)$",
            puno_ime,
        ):
            return match.group(1), match.group(2)

        return None, None
