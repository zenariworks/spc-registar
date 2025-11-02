"""Правила поста за 2025. годину и помоћне функције.

Ова имплементација користи датуме из календара поста за 2025. годину
(референца: Crkveni kalendar – Православни календар поста за 2025.)
и своди информацију на: да ли је конкретни дан пост или није.

Напомена: Правила поста могу имати локалне изузетке. Ово је практична,
једноставна процена погодна за приказ у апликацији.
"""

from __future__ import annotations

import datetime as dt


def orthodox_pascha_2025() -> dt.date:
    """Враћа датум Васкрса (Пасхе) за 2025. годину за потребе календара.

    За 2025. годину Пасха је 20. април.
    """

    return dt.date(2025, 4, 20)


def _date_range(start: dt.date, end: dt.date) -> set[dt.date]:
    """Скуп датума у затвореном интервалу [start, end]."""
    days = set()
    cur = start
    while cur <= end:
        days.add(cur)
        cur = cur + dt.timedelta(days=1)
    return days


def fasting_days_2025() -> set[dt.date]:
    """Скуп дана који су у посту током 2025. године.

    Обухвата:
    - Божићни пост: 1–6. јануар 2025. и 28. новембар – 31. децембар 2025.
    - Велики пост: 3. март – 19. април 2025.
    - Бели мрс: 24. фебруар – 2. март 2025. (делимични пост – без меса).
    - Апостолски пост: 16. јун – 11. јул 2025.
    - Крстовдан: 18. јануар 2025.
    - Сваке среде и петка (осим у „трапавим“ седмицама – видети ниже).
    """

    pascha = orthodox_pascha_2025()

    # Фиксни периоди поста
    ranges = [
        _date_range(dt.date(2025, 1, 1), dt.date(2025, 1, 6)),
        _date_range(dt.date(2025, 3, 3), dt.date(2025, 4, 19)),
        _date_range(dt.date(2025, 2, 24), dt.date(2025, 3, 2)),  # Бели мрс
        _date_range(dt.date(2025, 6, 16), dt.date(2025, 7, 11)),
        _date_range(dt.date(2025, 11, 28), dt.date(2025, 12, 31)),
    ]

    # Појединачни дани
    singles = {dt.date(2025, 1, 18)}  # Крстовдан

    fasting = set().union(*ranges).union(singles)

    # Трапаве седмице (без среде и петка као постних дана)
    trapave_ranges = [
        _date_range(dt.date(2025, 1, 7), dt.date(2025, 1, 17)),  # После Божића до Крстовдана
        _date_range(pascha + dt.timedelta(days=1), pascha + dt.timedelta(days=7)),  # Светла седмица: 21–27. април
        _date_range(dt.date(2025, 6, 9), dt.date(2025, 6, 15)),  # Седмица после Духова
        _date_range(dt.date(2025, 2, 10), dt.date(2025, 2, 16)),  # Митар и Фарисеј (pre-Lent fast-free)
    ]
    trapave = set().union(*trapave_ranges)

    # Додај сваке среде и петка као пост, осим у трававим седмицама
    year_days = _date_range(dt.date(2025, 1, 1), dt.date(2025, 12, 31))
    for d in year_days:
        if d.weekday() in (2, 4):  # 0=пон, 2=сре, 4=пет
            if d not in trapave:
                fasting.add(d)

    return fasting


def is_fasting_day(date: dt.date) -> bool:
    """Да ли је дати датум пост за 2025. годину."""
    if date.year != 2025:
        # За друге године применити само опште правило: среда/петак као постни дани
        # (без обраде изузетака).
        return date.weekday() in (2, 4)
    return date in fasting_days_2025()