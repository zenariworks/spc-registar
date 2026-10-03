"""
Тестови за православни календар поста и рачунање Васкрса.

Покрива:
- sracunaj_vaskrs: Гаусов алгоритам за православни Васкрс
- tip_posta: одређивање типа поста за датум
- je_post: да ли је датум постни дан
- Велики пост, Божићни пост, Успенски пост, Апостолски пост
- Трапаве седмице (без поста)
- Среда и петак (општи пост)

Већина провера је за 2026. годину, када је Васкрс 12. априла.
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

GODINA = 2026
GODINE = range(2020, 2030)
PONEDELJAK, SREDA, NEDELJA = 0, 2, 6


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
        for dan in unutra:
            self.assertIn(dan, dani)
        for dan in van:
            self.assertNotIn(dan, dani)

    def assert_post(self, dan, tip):
        """tip_posta: дан је постни, задатог типа."""
        rezultat = tip_posta(dan)
        self.assertTrue(rezultat["je_post"])
        self.assertEqual(rezultat["type"], tip)

    def assert_nije_post(self, dan):
        """tip_posta: дан није постни."""
        self.assertFalse(tip_posta(dan)["je_post"])


class CalcVaskrsTestCase(TestCase):
    """Тестови за рачунање православног Васкрса (Гаусов алгоритам)."""

    def test_known_easter_dates(self):
        """Познати датуми православног Васкрса (timeanddate.com, orthodox-easter-day)."""
        poznati_datumi = {
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
        for godina, (mesec, dan) in poznati_datumi.items():
            with self.subTest(godina=godina):
                self.assertEqual(
                    Slava.sracunaj_vaskrs(godina), datum(mesec, dan, godina)
                )

    def test_easter_always_sunday(self):
        """Васкрс увек пада у недељу."""
        for godina in range(2000, 2050):
            vaskrs = Slava.sracunaj_vaskrs(godina)
            self.assertEqual(
                vaskrs.weekday(), NEDELJA, f"Васкрс {godina} ({vaskrs}) није недеља"
            )

    def test_easter_in_valid_range(self):
        """Васкрс пада између 22. марта и 8. маја (грегоријански)."""
        for godina in range(1900, 2100):
            vaskrs = Slava.sracunaj_vaskrs(godina)
            self.assertTrue(
                datum(3, 22, godina) <= vaskrs <= datum(5, 8, godina),
                f"Васкрс {godina} ({vaskrs}) ван опсега",
            )

    def test_easter_never_repeats_same_date_too_often(self):
        """Васкрс не пада на исти датум више од 3 године заредом."""
        datumi = [Slava.sracunaj_vaskrs(godina) for godina in range(2000, 2100)]
        for i in range(len(datumi) - 3):
            self.assertFalse(
                datumi[i] == datumi[i + 1] == datumi[i + 2] == datumi[i + 3],
                f"Исти датум Васкрса 4 године заредом: {datumi[i]}",
            )


class GreatLentTestCase(_PostBase):
    """Тестови за Велики пост."""

    def test_great_lent_duration(self):
        """Велики пост траје 48 дана (Чисти понедељак до Велике суботе)."""
        for godina in GODINE:
            post = veliki_post(godina)
            self.assertEqual(len(post), 48, f"Велики пост {godina}: {len(post)} дана")

    def test_great_lent_ends_before_easter(self):
        """Велики пост се завршава дан пре Васкрса."""
        for godina in GODINE:
            self.assert_granice(
                veliki_post(godina),
                unutra=[od_vaskrsa(-1, godina)],
                van=[od_vaskrsa(0, godina)],
            )

    def test_great_lent_starts_clean_monday(self):
        """Велики пост почиње Чистим понедељком."""
        for godina in GODINE:
            self.assertIn(cisti_ponedeljak(godina), veliki_post(godina))
            self.assertEqual(cisti_ponedeljak(godina).weekday(), PONEDELJAK)

    def test_great_lent_2026(self):
        """Велики пост 2026: од Чистог понедељка 23. фебруара до Велике суботе 11. априла."""
        self.assert_granice(
            veliki_post(GODINA),
            unutra=[datum(2, 23), datum(4, 11)],
            van=[datum(4, 12), datum(2, 22)],
        )


class CheesefarWeekTestCase(_PostBase):
    """Тестови за Бели мрс (седмица пре Великог поста)."""

    def test_cheesefare_duration(self):
        """Бели мрс траје 7 дана."""
        for godina in GODINE:
            beli = beli_mrs(godina)
            self.assertEqual(len(beli), 7, f"Бели мрс {godina}: {len(beli)} дана")

    def test_cheesefare_ends_before_great_lent(self):
        """Бели мрс се завршава дан пре Великог поста."""
        for godina in GODINE:
            self.assert_granice(
                beli_mrs(godina),
                unutra=[cisti_ponedeljak(godina) - dt.timedelta(days=1)],
                van=[cisti_ponedeljak(godina)],
            )


class ApostlesFastTestCase(_PostBase):
    """Тестови за Апостолски (Петровдан) пост."""

    def test_apostles_fast_starts_after_pentecost(self):
        """Апостолски пост почиње понедељак после Духова."""
        for godina in GODINE:
            post = apostolski_post(godina)
            if not post:
                continue
            self.assertEqual(duhovi(godina).weekday(), NEDELJA)
            pocetak = duhovi(godina) + dt.timedelta(days=1)
            self.assertIn(pocetak, post)
            self.assertEqual(pocetak.weekday(), PONEDELJAK)

    def test_apostles_fast_ends_july_11(self):
        """Апостолски пост се завршава 11. јула (уочи Петровдана)."""
        for godina in GODINE:
            post = apostolski_post(godina)
            if not post:
                continue
            self.assert_granice(
                post, unutra=[datum(7, 11, godina)], van=[datum(7, 12, godina)]
            )

    def test_apostles_fast_variable_length(self):
        """Апостолски пост варира у дужини зависно од Васкрса."""
        duzine = {len(apostolski_post(godina)) for godina in GODINE}
        self.assertTrue(
            len(duzine) > 1, "Апостолски пост би требало да варира у дужини"
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
        """Трапава седмица после Педесетнице: од понедељка (Васкрс+50) до недеље (Васкрс+56), #253."""
        self.assertEqual(duhovi().weekday(), NEDELJA)
        self.assert_granice(
            trapave_sedmice(GODINA), unutra=[od_vaskrsa(i) for i in range(50, 57)]
        )

    def test_wednesday_in_trapava_not_fasting(self):
        """Среда у Светлој седмици (Васкрс+3) није постни дан."""
        sreda = od_vaskrsa(3)
        self.assertEqual(sreda.weekday(), SREDA)
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
        rezultat = tip_posta(datum(6, 15))
        for kljuc in ("je_post", "type", "display", "description"):
            self.assertIn(kljuc, rezultat)


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
        with CaptureQueriesContext(connection) as hladno:
            postni_dani_iz_baze(GODINA)
        self.assertGreaterEqual(len(hladno.captured_queries), 1)
        with CaptureQueriesContext(connection) as toplo:
            for _ in range(30):
                postni_dani_iz_baze(GODINA)
        self.assertEqual(len(toplo.captured_queries), 0)

    def test_je_post_loop_single_year_query(self):
        """je_post за 12 дана исте године чита постове из базе једном.

        Раније је било ~12 истоветних упита; дозвољен је и SET search_path.
        """
        with CaptureQueriesContext(connection) as upiti:
            for mesec in range(1, 13):
                je_post(datum(mesec, 15))
        self.assertLessEqual(len(upiti.captured_queries), 2)

    def test_year_functions_return_frozenset(self):
        """Годишње функције враћају frozenset (безбедно за кеш)."""
        for funkcija in (veliki_post, apostolski_post, postni_dani_iz_baze):
            self.assertIsInstance(funkcija(GODINA), frozenset)

    def test_clear_resets_cache(self):
        """obrisi_kes_posta празни кеш."""
        veliki_post(GODINA)
        self.assertGreaterEqual(veliki_post.cache_info().currsize, 1)
        obrisi_kes_posta()
        self.assertEqual(veliki_post.cache_info().currsize, 0)
