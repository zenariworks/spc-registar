"""
Парсер за нормализацију вероисповести и народности из слободног текста.

Легаси подаци из крштених записа садрже комбиновани текст за оба родитеља,
нпр. "Православни, Срби" или "Православни Србин и Римокатолкиња Мађарица".

Овај модул парсира такве текстове у структуриране податке.
"""

from __future__ import annotations

import re
from typing import Mapping, TypedDict


class OsobaPodaci(TypedDict):
    veroispovest: str | None
    narodnost: str | None


# Важно: дужи термини морају бити пре краћих јер се тражи substring.
VEROISPOVESTI = {
    "гркокатол": "Гркокатоличка",
    "римокатол": "Римокатоличка",
    "католк": "Римокатоличка",
    "католик": "Римокатоличка",
    "православн": "Православна",
    "правосл": "Православна",
    "прав.": "Православна",
    "прав ": "Православна",
    "праволавн": "Православна",
    "муслиман": "Ислам",
    "ислам": "Ислам",
    "протестан": "Протестантска",
    "методист": "Протестантска",
    "хришћан": "Хришћанска",
    "некрштен": "Некрштен",
    "атеист": "Атеиста",
}


NARODNOSTI = {
    "срб": "Српска",
    "српк": "Српска",
    "мађар": "Мађарска",
    "рус": "Руска",
    "бугар": "Бугарска",
    "хрват": "Хрватска",
    "словен": "Словеначка",
    "словак": "Словачка",
    "ром": "Ромска",
    "немц": "Немачка",
    "немки": "Немачка",
    "грк": "Грчка",
    "грчк": "Грчка",
    "данац": "Данска",
    "данки": "Данска",
    "норвеж": "Норвешка",
    "швеђ": "Шведска",
    "филипин": "Филипинска",
    "корeан": "Корејска",
    "јапан": "Јапанска",
    "америк": "Америчка",
    "британ": "Британска",
    "ирац": "Ирска",
    "холанђ": "Холандска",
    "француск": "Француска",
    "перуан": "Перуанска",
    "новозел": "Новозеландска",
    "либан": "Либанска",
    "чех": "Чешка",
    "турк": "Турска",
    "албан": "Албанска",
    "црногор": "Црногорска",
    "македон": "Македонска",
}


def _napravi_pretragu(
    mapa: Mapping[str, str],
) -> re.Pattern[str]:
    """Креира regex за препознавање кључних речи."""
    obrasci = "|".join(map(re.escape, mapa))
    return re.compile(obrasci, re.IGNORECASE)


_REGEX_VERA = _napravi_pretragu(VEROISPOVESTI)
_REGEX_NARODNOST = _napravi_pretragu(NARODNOSTI)


def _pronadji(
    tekst: str,
    mapa: Mapping[str, str],
    regex: re.Pattern[str],
) -> str | None:
    """Пронађи канонску вредност за прво пронађено поклапање."""
    match = regex.search(tekst.lower())

    if not match:
        return None

    return mapa[match.group()]


def _rasclani_segment(tekst: str) -> OsobaPodaci:
    """Парсира једну особу."""
    return {
        "veroispovest": _pronadji(
            tekst,
            VEROISPOVESTI,
            _REGEX_VERA,
        ),
        "narodnost": _pronadji(
            tekst,
            NARODNOSTI,
            _REGEX_NARODNOST,
        ),
    }


def rasclani_vera_narodnost(
    tekst: str | None,
) -> tuple[OsobaPodaci, OsobaPodaci | None]:
    """
    Парсира комбиновани текст вероисповести и народности.

    Враћа:
        (
            прва особа,
            друга особа или None
        )
    """

    prazno: OsobaPodaci = {
        "veroispovest": None,
        "narodnost": None,
    }

    if not (tekst := (tekst or "").strip()):
        return prazno, None

    osobe = [deo.strip() for deo in tekst.split(" и ", maxsplit=1)]

    prvi = _rasclani_segment(osobe[0])
    drugi = _rasclani_segment(osobe[1]) if len(osobe) == 2 else None

    return prvi, drugi


def get_canonical_vere() -> list[str]:
    """Врати канонске називе вероисповести."""
    return sorted(set(VEROISPOVESTI.values()))


def get_canonical_narodnosti() -> list[str]:
    """Врати канонске називе народности."""
    return sorted(set(NARODNOSTI.values()))
