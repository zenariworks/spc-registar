"""
Тестови за православни календар поста и рачунање Васкрса.

Покрива:
- sracunaj_vaskrs: Гаусов алгоритам за православни Васкрс
- tip_posta: одређивање типа поста за датум
- je_post: да ли је датум постни дан
- Велики пост, Божићни пост, Успенски пост, Апостолски пост
- Трапаве седмице (без поста)
- Среда и петак (општи пост)
"""

import datetime as dt

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from kalendar.models import Slava
from registar.utils.post import (
    apostolski_post,
    beli_mrs,
    fiksni_postovi,
    je_post,
    obrisi_kes_posta,
    postni_dani_iz_baze,
    tip_posta,
    trapave_sedmice,
    veliki_post,
)

GODINA = 2026  # Васкрс је 12. април
GODINE = range(2020, 2030)


def datum(mesec, dan, godina=GODINA):
    """Датум у години `godina` (подразумевано 2026)."""
    return dt.date(godina, mesec, dan)


def od_vaskrsa(dana, godina=GODINA):
    """Датум `dana` дана после Васкрса (негативно: пре Васкрса)."""
    return Slava.sracunaj_vaskrs(godina) + dt.timedelta(days=dana)


def cisti_ponedeljak(godina=GODINA):
    """Први дан Великог поста: Васкрс − 48."""
    return od_vaskrsa(-48, godina)


def duhovi(godina=GODINA):
    """Педесетница (Духови): Васкрс + 49, увек недеља."""
    return od_vaskrsa(49, godina)


class _PostBase(TestCase):
    """Заједничке провере за скупове постних дана и tip_posta."""

    def assert_granice(self, dani, unutra=(), van=()):
        """Сви датуми из `unutra` су у скупу, ниједан из `van` није."""
        for d in unutra:
            self.assertIn(d, dani)
        for d in van:
            self.assertNotIn(d, dani)

    def assert_post(self, dan, tip):
        """tip_posta: дан је постни, задатог типа."""
        result = tip_posta(dan)
        self.assertTrue(result["je_post"])
        self.assertEqual(result["type"], tip)

    def assert_nije_post(self, dan):
        """tip_posta: дан није постни."""
        self.assertFalse(tip_posta(dan)["je_post"])


class CalcVaskrsTestCase(TestCase):
    """Тестови за рачунање православног Васкрса (Гаусов алгоритам)."""

    def test_known_easter_dates(self):
        """Верификација познатих датума православног Васкрса."""
        # Извор: https://www.timeanddate.com/holidays/common/orthodox-easter-day
        known_dates = {
            2020: (4, 19),
            2021: (5, 2),
            2022: (4, 24),
            2023: (4, 16),
            2024: (5, 5),
            2025: (4, 20),
            2026: (4, 12),
            2027: (5, 2),
            2028: (4, 16),
            2029: (4, 8),
            2030: (4, 28),
        }
        for year, (mesec, dan) in known_dates.items():
            with self.subTest(year=year):
                self.assertEqual(Slava.sracunaj_vaskrs(year), datum(mesec, dan, year))

    def test_easter_always_sunday(self):
        """Васкрс увек пада у недељу."""
        for year in range(2000, 2050):
            vaskrs = Slava.sracunaj_vaskrs(year)
            self.assertEqual(
                vaskrs.weekday(), 6, f"Васкрс {year} ({vaskrs}) није недеља"
            )

    def test_easter_in_valid_range(self):
        """Васкрс пада између 22. марта и 8. маја (грегоријански)."""
        for year in range(1900, 2100):
            vaskrs = Slava.sracunaj_vaskrs(year)
            self.assertTrue(
                datum(3, 22, year) <= vaskrs <= datum(5, 8, year),
                f"Васкрс {year} ({vaskrs}) ван опсега",
            )

    def test_easter_never_repeats_same_date_too_often(self):
        """Васкрс не пада на исти датум више од 3 године заредом."""
        dates = [Slava.sracunaj_vaskrs(y) for y in range(2000, 2100)]
        for i in range(len(dates) - 3):
            self.assertFalse(
                dates[i] == dates[i + 1] == dates[i + 2] == dates[i + 3],
                f"Исти датум Васкрса 4 године заредом: {dates[i]}",
            )


class GreatLentTestCase(_PostBase):
    """Тестови за Велики пост."""

    def test_great_lent_duration(self):
        """Велики пост траје 48 дана (Чисти понедељак до Велике суботе)."""
        for year in GODINE:
            lent = veliki_post(year)
            self.assertEqual(len(lent), 48, f"Велики пост {year}: {len(lent)} дана")

    def test_great_lent_ends_before_easter(self):
        """Велики пост се завршава дан пре Васкрса."""
        for year in GODINE:
            self.assert_granice(
                veliki_post(year),
                unutra=[od_vaskrsa(-1, year)],
                van=[od_vaskrsa(0, year)],
            )

    def test_great_lent_starts_clean_monday(self):
        """Велики пост почиње Чистим понедељком."""
        for year in GODINE:
            self.assertIn(cisti_ponedeljak(year), veliki_post(year))
            self.assertEqual(cisti_ponedeljak(year).weekday(), 0)  # понедељак

    def test_great_lent_2026(self):
        """Велики пост 2026: 23. фебруар - 11. април."""
        self.assert_granice(
            veliki_post(GODINA),
            unutra=[datum(2, 23), datum(4, 11)],  # Чисти понедељак, Велика субота
            van=[datum(4, 12), datum(2, 22)],  # Васкрс, дан пре
        )


class CheesefarWeekTestCase(_PostBase):
    """Тестови за Бели мрс (седмица пре Великог поста)."""

    def test_cheesefare_duration(self):
        """Бели мрс траје 7 дана."""
        for year in GODINE:
            cheese = beli_mrs(year)
            self.assertEqual(len(cheese), 7, f"Бели мрс {year}: {len(cheese)} дана")

    def test_cheesefare_ends_before_great_lent(self):
        """Бели мрс се завршава дан пре Великог поста."""
        for year in GODINE:
            self.assert_granice(
                beli_mrs(year),
                unutra=[cisti_ponedeljak(year) - dt.timedelta(days=1)],
                van=[cisti_ponedeljak(year)],
            )


class ApostlesFastTestCase(_PostBase):
    """Тестови за Апостолски (Петровдан) пост."""

    def test_apostles_fast_starts_after_pentecost(self):
        """Апостолски пост почиње понедељак после Духова."""
        for year in GODINE:
            fast = apostolski_post(year)
            if not fast:
                continue
            self.assertEqual(duhovi(year).weekday(), 6)  # недеља
            expected_start = duhovi(year) + dt.timedelta(days=1)
            self.assertIn(expected_start, fast)
            self.assertEqual(expected_start.weekday(), 0)  # понедељак

    def test_apostles_fast_ends_july_11(self):
        """Апостолски пост се завршава 11. јула (Петровдан eve)."""
        for year in GODINE:
            fast = apostolski_post(year)
            if not fast:
                continue
            self.assert_granice(
                fast, unutra=[datum(7, 11, year)], van=[datum(7, 12, year)]
            )

    def test_apostles_fast_variable_length(self):
        """Апостолски пост варира у дужини зависно од Васкрса."""
        lengths = {len(apostolski_post(year)) for year in GODINE}
        self.assertTrue(
            len(lengths) > 1, "Апостолски пост би требало да варира у дужини"
        )


class FixedFastingTestCase(_PostBase):
    """Тестови за фиксне постне периоде."""

    def test_christmas_fast_november(self):
        """Божићни пост почиње 28. новембра."""
        self.assert_granice(
            fiksni_postovi(GODINA), unutra=[datum(11, 28)], van=[datum(11, 27)]
        )

    def test_christmas_fast_january(self):
        """Божићни пост траје до 6. јануара."""
        self.assert_granice(
            fiksni_postovi(GODINA), unutra=[datum(1, 6)], van=[datum(1, 7)]
        )

    def test_dormition_fast(self):
        """Успенски пост: 14-27. август (грегоријански)."""
        self.assert_granice(
            fiksni_postovi(GODINA),
            unutra=[datum(8, 14), datum(8, 27)],
            van=[datum(8, 13), datum(8, 28)],
        )

    def test_krstovdan(self):
        """Крстовдан: 18. јануар."""
        self.assertIn(datum(1, 18), fiksni_postovi(GODINA))


class TrapaveWeeksTestCase(_PostBase):
    """Тестови за трапаве седмице (без поста)."""

    def test_bright_week_after_easter(self):
        """Светла седмица: 7 дана после Васкрса."""
        self.assert_granice(
            trapave_sedmice(GODINA), unutra=[od_vaskrsa(i) for i in range(1, 8)]
        )

    def test_post_christmas_trapava(self):
        """После Божића до Крстовдана: 7-17. јануар."""
        self.assert_granice(
            trapave_sedmice(GODINA),
            unutra=[datum(1, 7), datum(1, 17)],
            van=[datum(1, 18)],
        )

    def test_post_pentecost_trapava_starts_monday_after_duhovi(self):
        """Трапава седмица после Педесетнице почиње понедељак после Духова (#253)."""
        self.assertEqual(duhovi().weekday(), 6)  # недеља
        # понедељак (Васкрс+50) кроз недељу (Васкрс+56) после Духова су трапави
        self.assert_granice(
            trapave_sedmice(GODINA), unutra=[od_vaskrsa(i) for i in range(50, 57)]
        )

    def test_wednesday_in_trapava_not_fasting(self):
        """Среда у трапавој седмици није постни дан."""
        sreda = od_vaskrsa(3)  # Светла седмица почиње понедељком
        self.assertEqual(sreda.weekday(), 2)
        self.assertFalse(
            je_post(sreda), f"{sreda} је среда у Светлој седмици, не пости се"
        )


class GetFastingTypeTestCase(_PostBase):
    """Тестови за одређивање типа поста."""

    def test_easter_sunday_not_fasting(self):
        """Васкрс није постни дан."""
        self.assert_nije_post(od_vaskrsa(0))

    def test_great_lent_weekday_water(self):
        """Радни дан у Великом посту (Чисти понедељак): вода."""
        self.assert_post(cisti_ponedeljak(), "вода")

    def test_great_lent_weekend_oil(self):
        """Субота/недеља у Великом посту (прва субота): уље."""
        self.assert_post(cisti_ponedeljak() + dt.timedelta(days=5), "уље")

    def test_annunciation_in_lent_fish(self):
        """Благовести (7. април) у Великом посту: риба."""
        self.assert_post(datum(4, 7), "риба")

    def test_palm_sunday_fish(self):
        """Цвети (недеља пре Васкрса): риба."""
        self.assert_post(od_vaskrsa(-7), "риба")

    def test_lazarus_saturday_fish(self):
        """Лазарева субота: риба."""
        self.assert_post(od_vaskrsa(-8), "риба")

    def test_cheesefare_beli_mrs(self):
        """Бели мрс: дозвољено све осим меса."""
        self.assert_post(od_vaskrsa(-50), "бели_мрс")

    def test_christmas_fast_sochi_water(self):
        """Сочи дан (6. јануар): строг пост."""
        self.assert_post(datum(1, 6), "вода")

    def test_christmas_day_not_fasting(self):
        """Божић (7. јануар): није пост."""
        self.assert_nije_post(datum(1, 7))

    def test_dormition_transfiguration_fish(self):
        """Преображење (19. август) у Успенском посту: риба."""
        self.assert_post(datum(8, 19), "риба")

    def test_krstovdan_water(self):
        """Крстовдан (18. јануар): строг пост."""
        self.assert_post(datum(1, 18), "вода")

    def test_regular_wednesday_fasting(self):
        """Обична среда (1. јул, ван постова и трапавих седмица): вода."""
        self.assert_post(datum(7, 1), "вода")

    def test_regular_friday_fasting(self):
        """Обичан петак (3. јул): пост (вода)."""
        self.assert_post(datum(7, 3), "вода")

    def test_regular_monday_not_fasting(self):
        """Обични понедељак (7. септембар, ван поста): није пост."""
        self.assert_nije_post(datum(9, 7))

    def test_return_dict_structure(self):
        """Повратни речник увек има тачне кључеве."""
        result = tip_posta(datum(6, 15))
        for kljuc in ("je_post", "type", "display", "description"):
            self.assertIn(kljuc, result)


class IsFastingDayTestCase(TestCase):
    """Тестови за je_post функцију."""

    def test_easter_not_fasting(self):
        """Васкрс није постни дан."""
        self.assertFalse(je_post(od_vaskrsa(0)))

    def test_great_lent_je_post(self):
        """Дан у Великом посту (Чисти понедељак) је постни дан."""
        self.assertTrue(je_post(cisti_ponedeljak()))

    def test_regular_thursday_not_fasting(self):
        """Обични четвртак (10. септембар, ван поста): није постни дан."""
        self.assertFalse(je_post(datum(9, 10)))

    def test_christmas_fast_je_post(self):
        """Дан у Божићном посту је постни дан."""
        self.assertTrue(je_post(datum(12, 1)))

    def test_dormition_fast_je_post(self):
        """Дан у Успенском посту је постни дан."""
        self.assertTrue(je_post(datum(8, 18)))


class FastingCacheTests(TestCase):
    """#257: годишњи прорачуни поста се кеширају (N+1 → 1 упит/прорачун)."""

    def setUp(self):
        obrisi_kes_posta()

    def test_db_fasting_days_cached_per_year(self):
        """Први позив чита базу, сваки следећи за исту годину не."""
        with CaptureQueriesContext(connection) as cold:
            postni_dani_iz_baze(GODINA)
        self.assertGreaterEqual(len(cold.captured_queries), 1)
        with CaptureQueriesContext(connection) as warm:
            for _ in range(30):
                postni_dani_iz_baze(GODINA)
        self.assertEqual(len(warm.captured_queries), 0)

    def test_je_post_loop_single_year_query(self):
        """je_post за 12 дана исте године не пита базу по позиву."""
        with CaptureQueriesContext(connection) as ctx:
            for mesec in range(1, 13):
                je_post(datum(mesec, 15))
        # Сви дани исте године → DB постови се читају једном, не по позиву
        # (раније ~12 истоветних упита). Допуштамо и SET search_path.
        self.assertLessEqual(len(ctx.captured_queries), 2)

    def test_year_functions_return_frozenset(self):
        """Годишње функције враћају frozenset (безбедно за кеш)."""
        for fn in (veliki_post, apostolski_post, postni_dani_iz_baze):
            self.assertIsInstance(fn(GODINA), frozenset)

    def test_clear_resets_cache(self):
        """obrisi_kes_posta празни кеш."""
        veliki_post(GODINA)
        self.assertGreaterEqual(veliki_post.cache_info().currsize, 1)
        obrisi_kes_posta()
        self.assertEqual(veliki_post.cache_info().currsize, 0)
