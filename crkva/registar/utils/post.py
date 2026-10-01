"""Правила поста - динамички рачунање на основу базе података.

Ова имплементација користи Slava модел са покретним празницима и
периодима поста за динамичко рачунање постних дана за било коју годину.

Напомена: Правила поста могу имати локалне изузетке. Ово је практична,
једноставна процена погодна за приказ у апликацији.
"""

from __future__ import annotations

import datetime as dt
from functools import lru_cache

from django_tenants.utils import schema_context

PON, UTO, SRE, CET, PET, SUB, NED = range(7)
VIKEND = (SUB, NED)
SREDA_I_PETAK = (SRE, PET)

KRSTOVDAN = (1, 18)
SOCIVO = (1, 6)
BLAGOVESTI = (4, 7)
PREOBRAZENJE = (8, 19)

NIJE_POST = {"je_post": False, "type": None, "display": None, "description": None}
VODA = {
    "je_post": True,
    "type": "вода",
    "display": "Вода",
    "description": "Пост без уља и рибе",
}
ULJE = {
    "je_post": True,
    "type": "уље",
    "display": "Уље",
    "description": "Дозвољени: уље и вино",
}
RIBA = {
    "je_post": True,
    "type": "риба",
    "display": "Риба",
    "description": "Дозвољени: уље, вино и риба",
}
BELI_MRS = {
    "je_post": True,
    "type": "бели_мрс",
    "display": "Бели мрс",
    "description": "Дозвољено све осим меса",
}

BOZICNI_POST_PO_DANU = {
    PON: VODA,
    UTO: ULJE,
    SRE: VODA,
    CET: ULJE,
    PET: VODA,
    SUB: RIBA,
    NED: RIBA,
}
USPENSKI_POST_PO_DANU = {
    PON: ULJE,
    UTO: ULJE,
    SRE: VODA,
    CET: ULJE,
    PET: VODA,
    SUB: RIBA,
    NED: RIBA,
}
APOSTOLSKI_POST_PO_DANU = {
    PON: ULJE,
    UTO: RIBA,
    SRE: VODA,
    CET: RIBA,
    PET: VODA,
    SUB: RIBA,
    NED: RIBA,
}


def _opseg_datuma(pocetak: dt.date, kraj: dt.date) -> set[dt.date]:
    """Скуп датума у затвореном интервалу [pocetak, kraj]."""
    days = set()
    cur = pocetak
    while cur <= kraj:
        days.add(cur)
        cur = cur + dt.timedelta(days=1)
    return days


def _vaskrs(godina: int) -> dt.date:
    """Датум Васкрса (грегоријански) за дату годину."""
    from registar.models import Slava

    return Slava.sracunaj_vaskrs(godina)


def _cisti_ponedeljak(godina: int) -> dt.date:
    """Чисти понедељак, први дан Великог поста: 48 дана пре Васкрса."""
    return _vaskrs(godina) - dt.timedelta(days=48)


def _duhovi(godina: int) -> dt.date:
    """Духови (Педесетница): 49 дана после Васкрса, увек недеља."""
    return _vaskrs(godina) + dt.timedelta(days=49)


@lru_cache(maxsize=128)
def postni_dani_iz_baze(godina: int) -> frozenset[dt.date]:
    """Врати скуп постних дана за дату годину из базе података.

    Резултат зависи само од године (Slava подаци су статични) па се кешира
    по години — рендер месеца тако издаје 1 уместо ~30 истоветних упита
    (#257). Slava живи у public шеми (дељени модел), па се чита у
    schema_context("public") да буде исти за све закупце и безбедан за кеш.
    """
    from registar.models import Slava

    postni_dani = set()
    with schema_context("public"):
        for post in Slava.objects.filter(post=True):
            period = post.get_post(godina)
            if period and period[0] and period[1]:
                pocetak, kraj = period
                postni_dani.update(_opseg_datuma(pocetak, kraj))

    return frozenset(postni_dani)


@lru_cache(maxsize=128)
def fiksni_postovi(godina: int) -> frozenset[dt.date]:
    """Врати фиксне постне периоде (који се не рачунају из базе).

    - Божићни пост: 28. новембар – 6. јануар (оба дела унутар дате године:
      28.11–31.12 и 1.1–6.1)
    - Успенски пост: 14–27. август (грегоријански)
    - Крстовдан: 18. јануар
    """
    postni_dani = set()
    postni_dani.update(_opseg_datuma(dt.date(godina, 11, 28), dt.date(godina, 12, 31)))
    postni_dani.update(_opseg_datuma(dt.date(godina, 1, 1), dt.date(godina, *SOCIVO)))
    postni_dani.update(_opseg_datuma(dt.date(godina, 8, 14), dt.date(godina, 8, 27)))
    postni_dani.add(dt.date(godina, *KRSTOVDAN))
    return frozenset(postni_dani)


@lru_cache(maxsize=128)
def apostolski_post(godina: int) -> frozenset[dt.date]:
    """Врати Апостолски (Петровдан) пост за дату годину.

    Почиње понедељак после Духова (Педесетнице) и траје до 11. јула
    (укључујући). Ако Духови падну касно, пост је празан.
    """
    pocetak = _duhovi(godina) + dt.timedelta(days=1)
    kraj = dt.date(godina, 7, 11)
    if pocetak > kraj:
        return frozenset()
    return frozenset(_opseg_datuma(pocetak, kraj))


@lru_cache(maxsize=128)
def beli_mrs(godina: int) -> frozenset[dt.date]:
    """Врати Бели мрс: седмицу пре Чистог понедељка (пост без меса)."""
    cisti_ponedeljak = _cisti_ponedeljak(godina)
    return frozenset(
        _opseg_datuma(
            cisti_ponedeljak - dt.timedelta(days=7),
            cisti_ponedeljak - dt.timedelta(days=1),
        )
    )


@lru_cache(maxsize=128)
def veliki_post(godina: int) -> frozenset[dt.date]:
    """Врати Велики пост за дату годину.

    Почиње Чистим понедељком (48 дана пре Васкрса) и
    траје до Велике суботе (1 дан пре Васкрса).
    """
    return frozenset(
        _opseg_datuma(_cisti_ponedeljak(godina), _vaskrs(godina) - dt.timedelta(days=1))
    )


@lru_cache(maxsize=128)
def trapave_sedmice(godina: int) -> frozenset[dt.date]:
    """Врати трапаве седмице (седмице без поста) за дату годину.

    - Светла седмица: седам дана после Васкрса
    - седмица после Духова
    - Митар и Фарисеј: седмица која почиње 3 недеље пре Чистог понедељка
    - од Божића до Крстовдана: 7–17. јануар
    """
    vaskrs = _vaskrs(godina)
    duhovi = _duhovi(godina)
    mitar_i_farisej = _cisti_ponedeljak(godina) - dt.timedelta(days=21)

    trapave = set()
    trapave.update(
        _opseg_datuma(vaskrs + dt.timedelta(days=1), vaskrs + dt.timedelta(days=7))
    )
    trapave.update(
        _opseg_datuma(duhovi + dt.timedelta(days=1), duhovi + dt.timedelta(days=7))
    )
    trapave.update(
        _opseg_datuma(mitar_i_farisej, mitar_i_farisej + dt.timedelta(days=6))
    )
    trapave.update(_opseg_datuma(dt.date(godina, 1, 7), dt.date(godina, 1, 17)))
    return frozenset(trapave)


def obrisi_kes_posta() -> None:
    """Очисти годишње кешеве поста.

    Позвати после измене Slava `post` података (нпр. reseed) или у тестовима
    који мењају DB постове, да се не послужи устајали резултат.
    """
    for fn in (
        postni_dani_iz_baze,
        fiksni_postovi,
        apostolski_post,
        beli_mrs,
        veliki_post,
        trapave_sedmice,
    ):
        fn.cache_clear()


def je_post(datum: dt.date) -> bool:
    """Да ли је дати датум пост.

    Пост је ако дан припада неком посном периоду (из базе, фиксном,
    Великом, Апостолском или Белом мрсу), или ако је среда/петак ван
    трапаве седмице.
    """
    godina = datum.year
    periodi = (
        postni_dani_iz_baze,
        fiksni_postovi,
        veliki_post,
        apostolski_post,
        beli_mrs,
    )
    if any(datum in period(godina) for period in periodi):
        return True
    return datum.weekday() in SREDA_I_PETAK and datum not in trapave_sedmice(godina)


def _dan_u_godini(datum: dt.date) -> tuple[int, int]:
    return (datum.month, datum.day)


def _u_bozicnom_postu(datum: dt.date) -> bool:
    """Божићни пост: 28. новембар – 6. јануар."""
    return (
        (datum.month == 11 and datum.day >= 28)
        or datum.month == 12
        or (datum.month == 1 and datum.day <= SOCIVO[1])
    )


def _u_uspenskom_postu(datum: dt.date) -> bool:
    """Успенски пост: 14–27. август (грегоријански)."""
    return datum.month == 8 and 14 <= datum.day <= 27


def _dan_velikog_posta(datum: dt.date) -> dict:
    """Риба на Благовести, Лазареву суботу и Цвети; уље викендом; иначе вода."""
    vaskrs = _vaskrs(datum.year)
    lazareva_subota = vaskrs - dt.timedelta(days=8)
    cveti = vaskrs - dt.timedelta(days=7)
    if _dan_u_godini(datum) == BLAGOVESTI or datum in (lazareva_subota, cveti):
        return RIBA
    if datum.weekday() in VIKEND:
        return ULJE
    return VODA


def _dan_bozicnog_posta(datum: dt.date) -> dict:
    """Бадњи дан (Сочиво, 6. јануар) је строг пост; остало по дану у недељи."""
    if _dan_u_godini(datum) == SOCIVO:
        return VODA
    return BOZICNI_POST_PO_DANU[datum.weekday()]


def _dan_uspenskog_posta(datum: dt.date) -> dict:
    """Преображење (19. август) је риба; остало по дану у недељи."""
    if _dan_u_godini(datum) == PREOBRAZENJE:
        return RIBA
    return USPENSKI_POST_PO_DANU[datum.weekday()]


def _vrsta_posta(datum: dt.date) -> dict:
    """Шаблон резултата за дати датум, по првом посном правилу које важи.

    Редослед провере: трапава седмица, Велики пост, Бели мрс, Божићни,
    Успенски, Апостолски пост, Крстовдан, па општи пост среда/петак.
    """
    godina = datum.year
    if datum in trapave_sedmice(godina):
        return NIJE_POST
    if datum in veliki_post(godina):
        return _dan_velikog_posta(datum)
    if datum in beli_mrs(godina):
        return BELI_MRS
    if _u_bozicnom_postu(datum):
        return _dan_bozicnog_posta(datum)
    if _u_uspenskom_postu(datum):
        return _dan_uspenskog_posta(datum)
    if datum in apostolski_post(godina):
        return APOSTOLSKI_POST_PO_DANU[datum.weekday()]
    if _dan_u_godini(datum) == KRSTOVDAN or datum.weekday() in SREDA_I_PETAK:
        return VODA
    return NIJE_POST


def tip_posta(datum: dt.date) -> dict[str, str | bool]:
    """Врати тип поста и дозвољена јела за дати датум.

    Враћа речник са следећим кључевима:
    - 'je_post': Да ли је постни дан (True/False)
    - 'type': Тип поста ('вода', 'уље', 'риба', 'бели_мрс', None)
    - 'display': Текст за приказ ('Вода', 'Уље', 'Риба', 'Бели мрс', None)
    - 'description': Опис дозвољених јела
    """
    return dict(_vrsta_posta(datum))
