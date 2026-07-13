"""
Пресловљавање латиница ↔ ћирилица (српски) и DBF конвертори.

Садржи:
- ``latin_to_cyrillic`` / ``cyrillic_to_latin`` — стандардна транслитерација.
- ``get_query_variants`` — варијанте упита за претрагу (латиница без
  дијакритика се разграна у све смислене ћириличне облике).
- ``Konvertor`` — помоћне статичке методе за миграцију из legacy DBF фајлова
  (укључујући стару HramSP/YUSCII енкодирану латиницу).

Дели заједничку мапу ``LATINICA_CIRILICA`` и листу дводелних слова ``DIGRAFI``
између стандардне транслитерације и ``Konvertor.string``.
"""

import logging
import re
from datetime import date

logger = logging.getLogger(__name__)


# --- Заједничке мапе ---
# Дводелна слова која важе за обе стране (стандардна и legacy латиница).
DIGRAFI = [
    ("DŽ", "Џ"),
    ("Dž", "Џ"),
    ("dž", "џ"),
    ("NJ", "Њ"),
    ("Nj", "Њ"),
    ("nj", "њ"),
    ("LJ", "Љ"),
    ("Lj", "Љ"),
    ("lj", "љ"),
]

# Дводелна слова само за кориснички унос: тастатуре без đ куцају "dj", а
# дијакритици се третирају као замене пре мапе појединачних слова.
DIGRAFI_UNOS = DIGRAFI + [
    ("Đ", "Ђ"),
    ("đ", "ђ"),
    # Честа замена кад је тастатура без đ: "dj" → "ђ"
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
]

# Канонско мапирање појединачних слова стандардне српске латинице у ћирилицу
# (укључујући дијакритике). Не мапирамо Q/W/X/Y — нису део српске латинице
# (у legacy HramSP енкодингу они имају засебно значење, види _HRAMSP_LEGACY).
LATINICA_CIRILICA = {
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


# --- Транслитерација латинице ↔ ћирилице (српски) ---
def latin_to_cyrillic(text: str) -> str:
    """
    Преводи српску латиницу у ћирилицу.

    Подржани су диграфи/триграфи: dž/Dž/DŽ, nj/Nj/NJ, lj/Lj/LJ, као и слова са
    дијакритицима: š/Š, č/Č, ć/Ć, ž/Ž, đ/Đ. Такође мапира основна латинична
    слова на ћирилична еквивалентна (a→а, b→б, ... j→ј, c→ц, итд.).

    Напомена: не покушавамо да преводимо енглеска слова попут "w", "y", "x"
    јер нису део српске латинице – остављају се како јесу.
    """
    if not text:
        return text

    # Прво заменити сложене комбинације да се не разбију појединачним словима
    out = text
    for src, dst in DIGRAFI_UNOS:
        out = out.replace(src, dst)

    return "".join(LATINICA_CIRILICA.get(ch, ch) for ch in out)


def preslovljavanje(text: str) -> str:
    """
    Преводи српску ћирилицу у латиницу, укључујући ђ/Ћ/Џ/Љ/Њ/Ш/Ч/Ћ/Ж.
    """
    if not text:
        return text

    # Мапирање појединачних ћириличних слова
    single_map = {
        "А": "A",
        "а": "a",
        "Б": "B",
        "б": "b",
        "В": "V",
        "в": "v",
        "Г": "G",
        "г": "g",
        "Д": "D",
        "д": "d",
        "Е": "E",
        "е": "e",
        "З": "Z",
        "з": "z",
        "И": "I",
        "и": "i",
        "Ј": "J",
        "ј": "j",
        "К": "K",
        "к": "k",
        "Л": "L",
        "л": "l",
        "М": "M",
        "м": "m",
        "Н": "N",
        "н": "n",
        "О": "O",
        "о": "o",
        "П": "P",
        "п": "p",
        "Р": "R",
        "р": "r",
        "С": "S",
        "с": "s",
        "Т": "T",
        "т": "t",
        "У": "U",
        "у": "u",
        "Ф": "F",
        "ф": "f",
        "Х": "H",
        "х": "h",
        "Ц": "C",
        "ц": "c",
        "Ш": "Š",
        "ш": "š",
        "Ч": "Č",
        "ч": "č",
        "Ћ": "Ć",
        "ћ": "ć",
        "Ж": "Ž",
        "ж": "ž",
        "Ђ": "Đ",
        "ђ": "đ",
        "Џ": "Dž",
        "џ": "dž",
        "Љ": "Lj",
        "љ": "lj",
        "Њ": "Nj",
        "њ": "nj",
    }
    return "".join(single_map.get(ch, ch) for ch in text)


# --- Експанзија варијанти за латиницу без дијакритика ---
# Корисници често куцају "kalicanin" уместо "kaličanin" / "Каличанин".
# Када латиница нема дијакритике, једно слово (c, s, z, d) може стајати
# за више ћириличних знакова. Овде генеришемо све смислене варијанте.

_LATIN_AMBIGUOUS_LETTERS = {
    "c": ["ц", "ч", "ћ"],
    "C": ["Ц", "Ч", "Ћ"],
    "s": ["с", "ш"],
    "S": ["С", "Ш"],
    "z": ["з", "ж"],
    "Z": ["З", "Ж"],
    "d": ["д", "ђ"],
    "D": ["Д", "Ђ"],
}

_LATIN_SIMPLE_MAP = {
    "A": "А",
    "a": "а",
    "B": "Б",
    "b": "б",
    "V": "В",
    "v": "в",
    "G": "Г",
    "g": "г",
    "E": "Е",
    "e": "е",
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
    "T": "Т",
    "t": "т",
    "U": "У",
    "u": "у",
    "F": "Ф",
    "f": "ф",
    "H": "Х",
    "h": "х",
}

_LATIN_VARIANT_CAP = 64


def _latin_to_cyrillic_variants(text: str) -> list[str]:
    """Враћа све смислене ћириличне варијанте за латинични унос који може
    бити без дијакритика. Дводелна слова (dž/nj/lj/đ/š/č/ć/ž) се прво
    замењују, а онда се појединачна двосмислена слова (c, s, z, d)
    разгранавају у све могуће ћириличне еквиваленте.
    """
    if not text:
        return [text]
    intermediate = text
    for src, dst in DIGRAFI_UNOS:
        intermediate = intermediate.replace(src, dst)

    variants: list[str] = [""]
    for ch in intermediate:
        if ch in _LATIN_AMBIGUOUS_LETTERS:
            variants = [
                v + opt for v in variants for opt in _LATIN_AMBIGUOUS_LETTERS[ch]
            ]
        elif ch in _LATIN_SIMPLE_MAP:
            mapped = _LATIN_SIMPLE_MAP[ch]
            variants = [v + mapped for v in variants]
        else:
            variants = [v + ch for v in variants]
        if len(variants) > _LATIN_VARIANT_CAP:
            variants = variants[:_LATIN_VARIANT_CAP]
            break
    return variants


def get_query_variants(text: str) -> list[str]:
    """
    Враћа јединствене варијанте упита за претрагу:
    - оригинал
    - све ћириличне варијанте за латиницу без дијакритика (c/s/z/d → ц,ч,ћ / с,ш / з,ж / д,ђ)
    - ћирилица → латиница
    """
    if not text:
        return []
    variants = {text}
    variants.update(_latin_to_cyrillic_variants(text))
    variants.add(preslovljavanje(text))
    return [v for v in variants if v]


# --- Legacy HramSP/YUSCII енкодинг (само за миграцију из DBF фајлова) ---
# У старом HramSP запису поједини латинични знакови и симболи представљају
# ћирилична слова која иначе нису део стандардне латинице.
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


class Konvertor:
    """
    Utility class for converting legacy DBF data to Django model formats.

    Provides static methods for:
    - Latin to Cyrillic string conversion (including legacy HramSP encoding)
    - Safe integer conversion with defaults
    - Date parsing with zero-component handling
    - Full name splitting for Cyrillic names
    """

    @staticmethod
    def int(value, default=0):
        """
        Safely converts a string to an integer.

        Args:
            value: The value to convert (string or None)
            default: The default value to return if conversion fails (default: 0)

        Returns:
            int: The converted integer or the default value
        """
        if value is None:
            return default

        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Warning: '{value}' cannot be converted to an integer.")
            return default

    @staticmethod
    def string(text):
        """
        Converts Serbian Latin text to Cyrillic, including legacy HramSP encoding.

        Handles:
        - Standard Serbian Latin characters (a-z, č, ć, š, ž, đ)
        - Latin digraphs Lj/Nj/Dž (any case) → љ/њ/џ
        - Legacy HramSP special encoding (q→љ, w→њ, ]→Ћ, }→ћ, \\→Ђ, |→ђ, x→џ)
        - Already Cyrillic text (passes through unchanged)

        Дели ``LATINICA_CIRILICA`` са ``latin_to_cyrillic``; поврх ње наноси
        legacy HramSP знакове. За разлику од ``latin_to_cyrillic``, НЕ третира
        "dj" као ђ — у DBF запису ђ долази као ``\\``/``|``.

        Args:
            text (str): The text to convert

        Returns:
            str: Converted Cyrillic text or empty string
        """
        if not text:
            return ""

        text = text.strip()
        if not text:
            return ""

        for latinica, cirilica in DIGRAFI:
            text = text.replace(latinica, cirilica)

        mapa = {**LATINICA_CIRILICA, **_HRAMSP_LEGACY}
        return "".join(mapa.get(char, char) for char in text)

    @staticmethod
    def date(y, m, d):
        """
        Create a date from year/month/day components, replacing zeros with default values.

        Legacy DBF files often have zero values for missing date components.
        This method replaces them with safe defaults:
        - year=0 → 1900
        - month=0 → 1
        - day=0 → 1

        Args:
            y: Year (int or None)
            m: Month (int or None)
            d: Day (int or None)

        Returns:
            date: A valid date object with zero components replaced
        """
        # Handle None values by treating them as zeros
        year = y if y is not None else 0
        month = m if m is not None else 0
        day = d if d is not None else 0

        # Replace zero components with defaults
        if year == 0:
            year = 1900
        if month == 0:
            month = 1
        if day == 0:
            day = 1

        return date(year, month, day)

    @staticmethod
    def split_name(full_name):
        """
        Split a full Cyrillic name into first and last name.

        Handles two patterns:
        1. Space-separated: "Петар Петровић" → ("Петар", "Петровић")
        2. CamelCase Cyrillic (no space): "СлавицаЋуковић" → ("Славица", "Ћуковић")

        Args:
            full_name (str): The full name to split

        Returns:
            tuple: (first_name, last_name) or (None, None) if splitting fails
        """
        if not full_name or not (full_name := full_name.strip()):
            return None, None

        # 1. Standard split by space
        if " " in full_name:
            first, last = full_name.split(maxsplit=1)
            return first, last

        # 2. Split by uppercase Cyrillic letter in the middle (CamelCase)
        if match := re.match(
            r"^([А-ЯЂЈЉЊЋЏа-яђјљњћџ]+?)([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)$", full_name
        ):
            return match.group(1), match.group(2)

        # Can't split - return None, None
        return None, None
