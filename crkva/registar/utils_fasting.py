"""Правила поста - динамички рачунање на основу базе података.

Ова имплементација користи Slava модел са покретним празницима и
периодима поста за динамичко рачунање постних дана за било коју годину.

Напомена: Правила поста могу имати локалне изузетке. Ово је практична,
једноставна процена погодна за приказ у апликацији.
"""

from __future__ import annotations

import datetime as dt


def _date_range(start: dt.date, end: dt.date) -> set[dt.date]:
    """Скуп датума у затвореном интервалу [start, end]."""
    days = set()
    cur = start
    while cur <= end:
        days.add(cur)
        cur = cur + dt.timedelta(days=1)
    return days


def get_fasting_days_from_db(year: int) -> set[dt.date]:
    """Врати скуп постних дана за дату годину из базе података."""
    from registar.models import Slava

    fasting = set()

    # Узми све постове из базе
    postovi = Slava.objects.filter(post=True)

    for post in postovi:
        period = post.get_post(year)
        if period and period[0] and period[1]:
            start, end = period
            fasting.update(_date_range(start, end))

    return fasting


def get_fixed_fasting_periods(year: int) -> set[dt.date]:
    """Врати фиксне постне периоде (који се не рачунају из базе)."""
    fasting = set()

    # Божићни пост: 28. новембар – 6. јануар
    # Део у текућој години (28.11 - 31.12)
    fasting.update(_date_range(dt.date(year, 11, 28), dt.date(year, 12, 31)))
    # Део у следећој години (1.1 - 6.1)
    fasting.update(_date_range(dt.date(year, 1, 1), dt.date(year, 1, 6)))

    # Успенски пост (Dormition fast): 1-14. август
    fasting.update(_date_range(dt.date(year, 8, 1), dt.date(year, 8, 14)))

    # Крстовдан: 18. јануар (појединачни дан)
    fasting.add(dt.date(year, 1, 18))

    return fasting


def get_apostles_fast(year: int) -> set[dt.date]:
    """Врати Апостолски (Петровдан) пост за дату годину.

    Почиње понедељак после Духова (Педесетнице) и траје до 11. јула (Петровдан eve).
    """
    from registar.models import Slava

    vaskrs = Slava.calc_vaskrs(year)

    # Духови (Педесетница) су 50 дана после Васкрса
    duhovi = vaskrs + dt.timedelta(days=50)

    # Пост почиње следећег понедељка после Духова
    # Духови су увек недеља, тако да је следећи дан понедељак
    start = duhovi + dt.timedelta(days=1)

    # Пост траје до 11. јула (укључујући)
    end = dt.date(year, 7, 11)

    # Ако је почетак после краја (кратак пост), врати празан скуп
    if start > end:
        return set()

    return _date_range(start, end)


def get_cheesefare_week(year: int) -> set[dt.date]:
    """Врати Бели мрс (недеља пре Великог поста - делимични пост без меса)."""
    from registar.models import Slava

    vaskrs = Slava.calc_vaskrs(year)

    # Чисти понедељак је 48 дана пре Васкрса
    cisti_ponedeljak = vaskrs - dt.timedelta(days=48)

    # Бели мрс је недеља пре Чистог понедељка
    start = cisti_ponedeljak - dt.timedelta(days=7)
    end = cisti_ponedeljak - dt.timedelta(days=1)

    return _date_range(start, end)


def get_great_lent(year: int) -> set[dt.date]:
    """Врати Велики пост за дату годину.

    Почиње Чистим понедељком (48 дана пре Васкрса) и
    траје до Велике суботе (1 дан пре Васкрса).
    """
    from registar.models import Slava

    vaskrs = Slava.calc_vaskrs(year)

    # Чисти понедељак (Clean Monday) - 48 дана пре Васкрса
    start = vaskrs - dt.timedelta(days=48)

    # Велика субота (Great Saturday) - 1 дан пре Васкрса
    end = vaskrs - dt.timedelta(days=1)

    return _date_range(start, end)


def get_trapave_weeks(year: int) -> set[dt.date]:
    """Врати трапаве седмице (седмице без поста) за дату годину."""
    from registar.models import Slava

    vaskrs = Slava.calc_vaskrs(year)
    trapave = set()

    # Светла седмица (недеља после Васкрса)
    trapave.update(
        _date_range(vaskrs + dt.timedelta(days=1), vaskrs + dt.timedelta(days=7))
    )

    # Седмица после Духова (50 дана после Васкрса + 7 дана)
    duhovi = vaskrs + dt.timedelta(days=50)
    trapave.update(
        _date_range(duhovi + dt.timedelta(days=1), duhovi + dt.timedelta(days=7))
    )

    # Митар и Фарисеј (3 недеље пре Чистог понедељка)
    cisti_ponedeljak = vaskrs - dt.timedelta(days=48)
    mitar_i_farisej_start = cisti_ponedeljak - dt.timedelta(days=21)
    trapave.update(
        _date_range(mitar_i_farisej_start, mitar_i_farisej_start + dt.timedelta(days=6))
    )

    # После Божића до Крстовдана (7-17. јануар)
    trapave.update(_date_range(dt.date(year, 1, 7), dt.date(year, 1, 17)))

    return trapave


def is_fasting_day(date: dt.date) -> bool:
    """Да ли је дати датум пост."""
    year = date.year

    # Узми све постове из базе (додатни покретни постови)
    fasting_from_db = get_fasting_days_from_db(year)

    # Узми фиксне постове (Божићни, Успенски, Крстовдан)
    fixed_fasting = get_fixed_fasting_periods(year)

    # Узми Велики пост (покретан, базиран на Васкрсу)
    great_lent = get_great_lent(year)

    # Узми Апостолски пост (покретан, базиран на Духовима)
    apostles_fast = get_apostles_fast(year)

    # Узми Бели мрс (недеља пре Великог поста - делимични пост)
    cheesefare = get_cheesefare_week(year)

    # Ако је дан у било ком посту
    if (
        date in fasting_from_db
        or date in fixed_fasting
        or date in great_lent
        or date in apostles_fast
        or date in cheesefare
    ):
        return True

    # Провери да ли је среда или петак (општи пост)
    if date.weekday() in (2, 4):  # 0=пон, 2=сре, 4=пет
        # Провери да ли је у трапавој седмици
        trapave = get_trapave_weeks(year)
        if date not in trapave:
            return True

    return False


def get_fasting_type(date: dt.date) -> dict[str, str | bool]:
    """Врати тип поста и дозвољена јела за дати датум.

    Враћа речник са следећим кључевима:
    - 'is_fasting': Да ли је постни дан (True/False)
    - 'type': Тип поста ('вода', 'уље', 'риба', 'бели_мрс', None)
    - 'display': Текст за приказ ('Вода', 'Уље', 'Риба', 'Бели мрс', None)
    - 'description': Опис дозвољених јела
    """
    from registar.models import Slava

    year = date.year
    weekday = date.weekday()  # 0=пон, 1=уто, 2=сре, 3=чет, 4=пет, 5=суб, 6=нед

    # Провери да ли је у трапавој седмици (без поста)
    trapave = get_trapave_weeks(year)
    if date in trapave:
        return {"is_fasting": False, "type": None, "display": None, "description": None}

    # Велики пост (Great Lent)
    great_lent = get_great_lent(year)
    if date in great_lent:
        vaskrs = Slava.calc_vaskrs(year)

        # Проверa за Благовести (25. март) у Великом посту
        if date.month == 3 and date.day == 25:
            return {
                "is_fasting": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Лазарева субота (дан пре Цвети)
        lazareva_subota = vaskrs - dt.timedelta(days=8)
        if date == lazareva_subota:
            return {
                "is_fasting": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Цвети (Вrbica, недеља пре Васкрса)
        cveti = vaskrs - dt.timedelta(days=7)
        if date == cveti:
            return {
                "is_fasting": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Субота и недеља у Великом посту - уље и вино
        if weekday in (5, 6):  # субота или недеља
            return {
                "is_fasting": True,
                "type": "уље",
                "display": "Уље",
                "description": "Дозвољени: уље и вино",
            }

        # Други дани Великог поста - вода
        return {
            "is_fasting": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Бели мрс (Cheesefare week - недеља пре Великог поста)
    cheesefare = get_cheesefare_week(year)
    if date in cheesefare:
        return {
            "is_fasting": True,
            "type": "бели_мрс",
            "display": "Бели мрс",
            "description": "Дозвољено све осим меса",
        }

    # Божићни пост (Christmas Fast) - 28. новембар до 6. јануар
    if (
        (date.month == 11 and date.day >= 28)
        or (date.month == 12)
        or (date.month == 1 and date.day <= 6)
    ):
        # Провери изузетке (Божић 25.12 по Јулијанском = 7.1 по Грегоријанском)
        if date.month == 1 and date.day == 7:
            return {
                "is_fasting": False,
                "type": None,
                "display": None,
                "description": None,
            }

        # Сочи дан (6. јануар) - строг пост
        if date.month == 1 and date.day == 6:
            return {
                "is_fasting": True,
                "type": "вода",
                "display": "Вода",
                "description": "Пост без уља и рибе",
            }

        # Субота и недеља - риба
        if weekday in (5, 6):
            return {
                "is_fasting": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Уторак и четвртак - уље
        if weekday in (1, 3):
            return {
                "is_fasting": True,
                "type": "уље",
                "display": "Уље",
                "description": "Дозвољени: уље и вино",
            }

        # Понедељак, среда, петак - вода
        return {
            "is_fasting": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Успенски пост (Dormition Fast) - 1-14. август
    if date.month == 8 and 1 <= date.day <= 14:
        # Преображење (6. август) - риба
        if date.day == 6:
            return {
                "is_fasting": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Субота и недеља - риба
        if weekday in (5, 6):
            return {
                "is_fasting": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Среда и петак - вода
        if weekday in (2, 4):
            return {
                "is_fasting": True,
                "type": "вода",
                "display": "Вода",
                "description": "Пост без уља и рибе",
            }

        # Други дани - уље
        return {
            "is_fasting": True,
            "type": "уље",
            "display": "Уље",
            "description": "Дозвољени: уље и вино",
        }

    # Апостолски пост (Apostles' Fast)
    apostles_fast = get_apostles_fast(year)
    if date in apostles_fast:
        # Субота и недеља - риба
        if weekday in (5, 6):
            return {
                "is_fasting": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Уторак и четвртак - риба
        if weekday in (1, 3):
            return {
                "is_fasting": True,
                "type": "риба",
                "display": "Риба",
                "description": "Дозвољени: уље, вино и риба",
            }

        # Понедељак - уље
        if weekday == 0:
            return {
                "is_fasting": True,
                "type": "уље",
                "display": "Уље",
                "description": "Дозвољени: уље и вино",
            }

        # Среда и петак - вода
        return {
            "is_fasting": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Крстовдан (18. јануар) - вода
    if date.month == 1 and date.day == 18:
        return {
            "is_fasting": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Општи пост (среда и петак)
    if weekday in (2, 4):
        return {
            "is_fasting": True,
            "type": "вода",
            "display": "Вода",
            "description": "Пост без уља и рибе",
        }

    # Није постни дан
    return {"is_fasting": False, "type": None, "display": None, "description": None}
