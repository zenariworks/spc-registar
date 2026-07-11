"""
Utility modules for the registar app.

This module provides transliteration utilities and other helper functions.
Previously located in utils.py, now organized as a proper package.
"""

from kalendar.models.slava import MESECI  # noqa: F401


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
    replacements = [
        ("DŽ", "Џ"),
        ("Dž", "Џ"),
        ("dž", "џ"),
        ("NJ", "Њ"),
        ("Nj", "Њ"),
        ("nj", "њ"),
        ("LJ", "Љ"),
        ("Lj", "Љ"),
        ("lj", "љ"),
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

    out = text
    for src, dst in replacements:
        out = out.replace(src, dst)

    # Појединачна слова
    single_map = {
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
        "E": "Е",
        "e": "е",
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
        # Остала латинична слова (Q, W, X, Y) се не мапирају – остављамо их.
    }

    return "".join(single_map.get(ch, ch) for ch in out)


def cyrillic_to_latin(text: str) -> str:
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

_LATIN_DIGRAPH_REPLACEMENTS = [
    ("DŽ", "Џ"),
    ("Dž", "Џ"),
    ("dž", "џ"),
    ("NJ", "Њ"),
    ("Nj", "Њ"),
    ("nj", "њ"),
    ("LJ", "Љ"),
    ("Lj", "Љ"),
    ("lj", "љ"),
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
]

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
    for src, dst in _LATIN_DIGRAPH_REPLACEMENTS:
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
    variants.add(cyrillic_to_latin(text))
    return [v for v in variants if v]
