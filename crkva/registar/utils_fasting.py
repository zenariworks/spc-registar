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


def _opseg_datuma(pocetak: dt.date, kraj: dt.date) -> set[dt.date]:
    """Скуп датума у затвореном интервалу [pocetak, kraj]."""
    days = set()
    cur = pocetak
    while cur <= kraj:
        days.add(cur)
        cur = cur + dt.timedelta(days=1)
    return days


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
    """Врати фиксне постне периоде (који се не рачунају из базе)."""
    postni_dani = set()

    # Божићни пост: 28. новембар – 6. јануар
    # Део у текућој години (28.11 - 31.12)
    postni_dani.update(_opseg_datuma(dt.date(godina, 11, 28), dt.date(godina, 12, 31)))
    # Део у следећој години (1.1 - 6.1)
    postni_dani.update(_opseg_datuma(dt.date(godina, 1, 1), dt.date(godina, 1, 6)))

    # Успенски пост (Dormition fast): 1-14. август
    postni_dani.update(_opseg_datuma(dt.date(godina, 8, 1), dt.date(godina, 8, 14)))

    # Крстовдан: 18. јануар (појединачни дан)
    postni_dani.add(dt.date(godina, 1, 18))

    return frozenset(postni_dani)


@lru_cache(maxsize=128)
def apostolski_post(godina: int) -> frozenset[dt.date]:
    """Врати Апостолски (Петровдан) пост за дату годину.

    Почиње понедељак после Духова (Педесетнице) и траје до 11. јула (Петровдан eve).
    """
    from registar.models import Slava

    vaskrs = Slava.calc_vaskrs(godina)

    # Духови (Педесетница) су 49 дана после Васкрса (50. дан рачунајући Васкрс
    # као први дан), и увек падају у недељу.
    duhovi = vaskrs + dt.timedelta(days=49)

    # Пост почиње следећег понедељка после Духова
    # Духови су увек недеља, тако да је следећи дан понедељак
    pocetak = duhovi + dt.timedelta(days=1)

    # Пост траје до 11. јула (укључујући)
    kraj = dt.date(godina, 7, 11)

    # Ако је почетак после краја (кратак пост), врати празан скуп
    if pocetak > kraj:
        return frozenset()

    return frozenset(_opseg_datuma(pocetak, kraj))


@lru_cache(maxsize=128)
def beli_mrs(godina: int) -> frozenset[dt.date]:
    """Врати Бели мрс (недеља пре Великог поста - делимични пост без меса)."""
    from registar.models import Slava

    vaskrs = Slava.calc_vaskrs(godina)

    # Чисти понедељак је 48 дана пре Васкрса
    cisti_ponedeljak = vaskrs - dt.timedelta(days=48)

    # Бели мрс је недеља пре Чистог понедељка
    pocetak = cisti_ponedeljak - dt.timedelta(days=7)
    kraj = cisti_ponedeljak - dt.timedelta(days=1)

    return frozenset(_opseg_datuma(pocetak, kraj))


@lru_cache(maxsize=128)
def veliki_post(godina: int) -> frozenset[dt.date]:
    """Врати Велики пост за дату годину.

    Почиње Чистим понедељком (48 дана пре Васкрса) и
    траје до Велике суботе (1 дан пре Васкрса).
    """
    from registar.models import Slava

    vaskrs = Slava.calc_vaskrs(godina)

    # Чисти понедељак (Clean Monday) - 48 дана пре Васкрса
    pocetak = vaskrs - dt.timedelta(days=48)

    # Велика субота (Great Saturday) - 1 дан пре Васкрса
    kraj = vaskrs - dt.timedelta(days=1)

    return frozenset(_opseg_datuma(pocetak, kraj))


@lru_cache(maxsize=128)
def trapave_sedmice(godina: int) -> frozenset[dt.date]:
    """Врати трапаве седмице (седмице без поста) за дату годину."""
    from registar.models import Slava

    vaskrs = Slava.calc_vaskrs(godina)
    trapave = set()

    # Светла седмица (недеља после Васкрса)
    trapave.update(
        _opseg_datuma(vaskrs + dt.timedelta(days=1), vaskrs + dt.timedelta(days=7))
    )

    # Седмица после Духова (49 дана после Васкрса; недеља после је трапава)
    duhovi = vaskrs + dt.timedelta(days=49)
    trapave.update(
        _opseg_datuma(duhovi + dt.timedelta(days=1), duhovi + dt.timedelta(days=7))
    )

    # Митар и Фарисеј (3 недеље пре Чистог понедељка)
    cisti_ponedeljak = vaskrs - dt.timedelta(days=48)
    mitar_i_farisej_start = cisti_ponedeljak - dt.timedelta(days=21)
    trapave.update(
        _opseg_datuma(
            mitar_i_farisej_start, mitar_i_farisej_start + dt.timedelta(days=6)
        )
    )

    # После Божића до Крстовдана (7-17. јануар)
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
    """Да ли је дати датум пост."""
    godina = datum.year

    # Узми све постове из базе (додатни покретни постови)
    fasting_from_db = postni_dani_iz_baze(godina)

    # Узми фиксне постове (Божићни, Успенски, Крстовдан)
    fixed_fasting = fiksni_postovi(godina)

    # Узми Велики пост (покретан, базиран на Васкрсу)
    great_lent = veliki_post(godina)

    # Узми Апостолски пост (покретан, базиран на Духовима)
    apostles_fast = apostolski_post(godina)

    # Узми Бели мрс (недеља пре Великог поста - делимични пост)
    cheesefare = beli_mrs(godina)

    # Ако је дан у било ком посту
    if (
        datum in fasting_from_db
        or datum in fixed_fasting
        or datum in great_lent
        or datum in apostles_fast
        or datum in cheesefare
    ):
        return True

    # Провери да ли је среда или петак (општи пост)
    if datum.weekday() in (2, 4):  # 0=пон, 2=сре, 4=пет
        # Провери да ли је у трапавој седмици
        trapave = trapave_sedmice(godina)
        if datum not in trapave:
            return True

    return False


def tip_posta(datum: dt.date) -> dict[str, str | bool]:
    """Врати тип поста и дозвољена јела за дати датум.

    Враћа речник са следећим кључевима:
    - 'je_post': Да ли је постни дан (True/False)
    - 'type': Тип поста ('вода', 'уље', 'риба', 'бели_мрс', None)
    - 'display': Текст за приказ ('Вода', 'Уље', 'Риба', 'Бели мрс', None)
    - 'description': Опис дозвољених јела
    """
    from registar.models import Slava

    godina = datum.year
    dan_u_nedelji = datum.weekday()  # 0=пон, 1=уто, 2=сре, 3=чет, 4=пет, 5=суб, 6=нед

    # Провери да ли је у трапавој седмици (без поста)
    trapave = trapave_sedmice(godina)
    if datum in trapave:
        return {"je_post": False, "type": None, "display": None, "description": None}

    # Велики пост (Great Lent)
    great_lent = veliki_post(godina)
    if datum in great_lent:
        vaskrs = Slava.calc_vaskrs(godina)

        # Проверa за Благовести (25. март) у Великом посту
        if datum.month == 3 and datum.day == 25:
            return {
                "je_post": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Лазарева субота (дан пре Цвети)
        lazareva_subota = vaskrs - dt.timedelta(days=8)
        if datum == lazareva_subota:
            return {
                "je_post": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Цвети (Вrbica, недеља пре Васкрса)
        cveti = vaskrs - dt.timedelta(days=7)
        if datum == cveti:
            return {
                "je_post": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Субота и недеља у Великом посту - уље и вино
        if dan_u_nedelji in (5, 6):  # субота или недеља
            return {
                "je_post": True,
                "type": "уље",
                "display": "Уље",
                "description": "Дозвољени: уље и вино",
            }

        # Други дани Великог поста - вода
        return {
            "je_post": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Бели мрс (Cheesefare week - недеља пре Великог поста)
    cheesefare = beli_mrs(godina)
    if datum in cheesefare:
        return {
            "je_post": True,
            "type": "бели_мрс",
            "display": "Бели мрс",
            "description": "Дозвољено све осим меса",
        }

    # Божићни пост (Christmas Fast) - 28. новембар до 6. јануар
    if (
        (datum.month == 11 and datum.day >= 28)
        or (datum.month == 12)
        or (datum.month == 1 and datum.day <= 6)
    ):
        # Провери изузетке (Божић 25.12 по Јулијанском = 7.1 по Грегоријанском)
        if datum.month == 1 and datum.day == 7:
            return {
                "je_post": False,
                "type": None,
                "display": None,
                "description": None,
            }

        # Сочи дан (6. јануар) - строг пост
        if datum.month == 1 and datum.day == 6:
            return {
                "je_post": True,
                "type": "вода",
                "display": "Вода",
                "description": "Пост без уља и рибе",
            }

        # Субота и недеља - риба
        if dan_u_nedelji in (5, 6):
            return {
                "je_post": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Уторак и четвртак - уље
        if dan_u_nedelji in (1, 3):
            return {
                "je_post": True,
                "type": "уље",
                "display": "Уље",
                "description": "Дозвољени: уље и вино",
            }

        # Понедељак, среда, петак - вода
        return {
            "je_post": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Успенски пост (Dormition Fast) - 1-14. август
    if datum.month == 8 and 1 <= datum.day <= 14:
        # Преображење (6. август) - риба
        if datum.day == 6:
            return {
                "je_post": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Субота и недеља - риба
        if dan_u_nedelji in (5, 6):
            return {
                "je_post": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Среда и петак - вода
        if dan_u_nedelji in (2, 4):
            return {
                "je_post": True,
                "type": "вода",
                "display": "Вода",
                "description": "Пост без уља и рибе",
            }

        # Други дани - уље
        return {
            "je_post": True,
            "type": "уље",
            "display": "Уље",
            "description": "Дозвољени: уље и вино",
        }

    # Апостолски пост (Apostles' Fast)
    apostles_fast = apostolski_post(godina)
    if datum in apostles_fast:
        # Субота и недеља - риба
        if dan_u_nedelji in (5, 6):
            return {
                "je_post": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Уторак и четвртак - риба
        if dan_u_nedelji in (1, 3):
            return {
                "je_post": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Понедељак - уље
        if dan_u_nedelji == 0:
            return {
                "je_post": True,
                "type": "уље",
                "display": "Уље",
                "description": "Дозвољени: уље и вино",
            }

        # Среда и петак - вода
        return {
            "je_post": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Крстовдан (18. јануар) - вода
    if datum.month == 1 and datum.day == 18:
        return {
            "je_post": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Општи пост (среда и петак)
    if dan_u_nedelji in (2, 4):
        return {
            "je_post": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Није постни дан
    return {"je_post": False, "type": None, "display": None, "description": None}
