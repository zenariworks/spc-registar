"""
Пресловљавање латиница ↔ ћирилица (српски).

Садржи:
- ``preslovi(tekst, u="cir"|"lat")`` — транслитерација у оба смера.
- ``get_query_variants`` — варијанте упита за претрагу (подршка за латиницу без дијакритика).
"""

from __future__ import annotations

import logging
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
def preslovi(text: str | None, u: Literal["cir", "lat"] = "cir") -> str:
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


def _latin_to_cyrillic_variants(tekst: str) -> list[str]:
    """Генерише све разумне ћириличне варијанте за латиницу без дијакритика."""
    if not tekst:
        return [""]

    # Замени диграфе
    intermediate = tekst
    for src, dst in DIGRAFI_UNOS:
        intermediate = intermediate.replace(src, dst)

    # Генериши варијанте помоћу product (много читљивије од ручног loop-а)
    delovi = []
    for ch in intermediate:
        if ch in _LATIN_AMBIGUOUS:
            delovi.append(_LATIN_AMBIGUOUS[ch])
        elif ch in _LATIN_SIMPLE_MAP:
            delovi.append((_LATIN_SIMPLE_MAP[ch],))
        else:
            delovi.append((ch,))

    # Ограничимо експлозију
    verzije = ["".join(kombo) for kombo in product(*delovi)][:64]
    return verzije


def get_query_variants(tekst: str) -> list[str]:
    """Враћа јединствене варијанте за претрагу (оригинал + ћирилица + латиница)."""
    if not tekst:
        return []

    variante = {tekst}
    variante.update(_latin_to_cyrillic_variants(tekst))
    variante.add(preslovi(tekst, u="lat"))

    return sorted(v for v in variante if v)
