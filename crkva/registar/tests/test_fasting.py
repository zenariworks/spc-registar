"""
Тестови за православни календар поста и рачунање Васкрса.

Покрива:
- calc_vaskrs: Гаусов алгоритам за православни Васкрс
- get_fasting_type: одређивање типа поста за датум
- is_fasting_day: да ли је датум постни дан
- Велики пост, Божићни пост, Успенски пост, Апостолски пост
- Трапаве седмице (без поста)
- Среда и петак (општи пост)
"""

import datetime as dt

from django.test import TestCase
from kalendar.models import Slava
from registar.utils_fasting import (
    get_apostles_fast,
    get_cheesefare_week,
    get_fasting_type,
    get_fixed_fasting_periods,
    get_great_lent,
    get_trapave_weeks,
    is_fasting_day,
)


class CalcVaskrsTestCase(TestCase):
    """Тестови за рачунање православног Васкрса (Гаусов алгоритам)."""

    def test_known_easter_dates(self):
        """Верификација познатих датума православног Васкрса."""
        # Извор: https://www.timeanddate.com/holidays/common/orthodox-easter-day
        known_dates = {
            2020: dt.date(2020, 4, 19),
            2021: dt.date(2021, 5, 2),
            2022: dt.date(2022, 4, 24),
            2023: dt.date(2023, 4, 16),
            2024: dt.date(2024, 5, 5),
            2025: dt.date(2025, 4, 20),
            2026: dt.date(2026, 4, 12),
            2027: dt.date(2027, 5, 2),
            2028: dt.date(2028, 4, 16),
            2029: dt.date(2029, 4, 8),
            2030: dt.date(2030, 4, 28),
        }
        for year, expected in known_dates.items():
            with self.subTest(year=year):
                self.assertEqual(Slava.calc_vaskrs(year), expected)

    def test_easter_always_sunday(self):
        """Васкрс увек пада у недељу."""
        for year in range(2000, 2050):
            vaskrs = Slava.calc_vaskrs(year)
            self.assertEqual(
                vaskrs.weekday(), 6, f"Васкрс {year} ({vaskrs}) није недеља"
            )

    def test_easter_in_valid_range(self):
        """Васкрс пада између 22. марта и 8. маја (грегоријански)."""
        for year in range(1900, 2100):
            vaskrs = Slava.calc_vaskrs(year)
            day_of_year = vaskrs.timetuple().tm_yday
            mar_22 = dt.date(year, 3, 22).timetuple().tm_yday
            may_08 = dt.date(year, 5, 8).timetuple().tm_yday
            self.assertTrue(
                mar_22 <= day_of_year <= may_08,
                f"Васкрс {year} ({vaskrs}) ван опсега",
            )

    def test_easter_never_repeats_same_date_too_often(self):
        """Васкрс не пада на исти датум више од 3 године заредом."""
        dates = [Slava.calc_vaskrs(y) for y in range(2000, 2100)]
        for i in range(len(dates) - 3):
            self.assertFalse(
                dates[i] == dates[i + 1] == dates[i + 2] == dates[i + 3],
                f"Исти датум Васкрса 4 године заредом: {dates[i]}",
            )


class GreatLentTestCase(TestCase):
    """Тестови за Велики пост."""

    def test_great_lent_duration(self):
        """Велики пост траје 48 дана (Чисти понедељак до Велике суботе)."""
        for year in range(2020, 2030):
            lent = get_great_lent(year)
            self.assertEqual(len(lent), 48, f"Велики пост {year}: {len(lent)} дана")

    def test_great_lent_ends_before_easter(self):
        """Велики пост се завршава дан пре Васкрса."""
        for year in range(2020, 2030):
            vaskrs = Slava.calc_vaskrs(year)
            lent = get_great_lent(year)
            self.assertIn(vaskrs - dt.timedelta(days=1), lent)
            self.assertNotIn(vaskrs, lent)

    def test_great_lent_starts_clean_monday(self):
        """Велики пост почиње Чистим понедељком."""
        for year in range(2020, 2030):
            vaskrs = Slava.calc_vaskrs(year)
            lent = get_great_lent(year)
            clean_monday = vaskrs - dt.timedelta(days=48)
            self.assertIn(clean_monday, lent)
            self.assertEqual(clean_monday.weekday(), 0)  # понедељак

    def test_great_lent_2026(self):
        """Велики пост 2026: 23. фебруар - 11. април."""
        Slava.calc_vaskrs(2026)  # 12. април
        lent = get_great_lent(2026)
        self.assertIn(dt.date(2026, 2, 23), lent)  # Чисти понедељак
        self.assertIn(dt.date(2026, 4, 11), lent)  # Велика субота
        self.assertNotIn(dt.date(2026, 4, 12), lent)  # Васкрс
        self.assertNotIn(dt.date(2026, 2, 22), lent)  # дан пре


class CheesefarWeekTestCase(TestCase):
    """Тестови за Бели мрс (седмица пре Великог поста)."""

    def test_cheesefare_duration(self):
        """Бели мрс траје 7 дана."""
        for year in range(2020, 2030):
            cheese = get_cheesefare_week(year)
            self.assertEqual(len(cheese), 7, f"Бели мрс {year}: {len(cheese)} дана")

    def test_cheesefare_ends_before_great_lent(self):
        """Бели мрс се завршава дан пре Великог поста."""
        for year in range(2020, 2030):
            vaskrs = Slava.calc_vaskrs(year)
            cheese = get_cheesefare_week(year)
            clean_monday = vaskrs - dt.timedelta(days=48)
            self.assertNotIn(clean_monday, cheese)
            self.assertIn(clean_monday - dt.timedelta(days=1), cheese)


class ApostlesFastTestCase(TestCase):
    """Тестови за Апостолски (Петровдан) пост."""

    def test_apostles_fast_starts_after_pentecost(self):
        """Апостолски пост почиње понедељак после Духова."""
        for year in range(2020, 2030):
            vaskrs = Slava.calc_vaskrs(year)
            fast = get_apostles_fast(year)
            if not fast:
                continue
            duhovi = vaskrs + dt.timedelta(days=50)
            expected_start = duhovi + dt.timedelta(days=1)
            self.assertIn(expected_start, fast)
            self.assertEqual(expected_start.weekday(), 1)  # уторак

    def test_apostles_fast_ends_july_11(self):
        """Апостолски пост се завршава 11. јула (Петровдан eve)."""
        for year in range(2020, 2030):
            fast = get_apostles_fast(year)
            if not fast:
                continue
            self.assertIn(dt.date(year, 7, 11), fast)
            self.assertNotIn(dt.date(year, 7, 12), fast)

    def test_apostles_fast_variable_length(self):
        """Апостолски пост варира у дужини зависно од Васкрса."""
        lengths = set()
        for year in range(2020, 2030):
            fast = get_apostles_fast(year)
            lengths.add(len(fast))
        self.assertTrue(
            len(lengths) > 1, "Апостолски пост би требало да варира у дужини"
        )


class FixedFastingTestCase(TestCase):
    """Тестови за фиксне постне периоде."""

    def test_christmas_fast_november(self):
        """Божићни пост почиње 28. новембра."""
        fasting = get_fixed_fasting_periods(2026)
        self.assertIn(dt.date(2026, 11, 28), fasting)
        self.assertNotIn(dt.date(2026, 11, 27), fasting)

    def test_christmas_fast_january(self):
        """Божићни пост траје до 6. јануара."""
        fasting = get_fixed_fasting_periods(2026)
        self.assertIn(dt.date(2026, 1, 6), fasting)
        self.assertNotIn(dt.date(2026, 1, 7), fasting)

    def test_dormition_fast(self):
        """Успенски пост: 1-14. август."""
        fasting = get_fixed_fasting_periods(2026)
        self.assertIn(dt.date(2026, 8, 1), fasting)
        self.assertIn(dt.date(2026, 8, 14), fasting)
        self.assertNotIn(dt.date(2026, 7, 31), fasting)
        self.assertNotIn(dt.date(2026, 8, 15), fasting)

    def test_krstovdan(self):
        """Крстовдан: 18. јануар."""
        fasting = get_fixed_fasting_periods(2026)
        self.assertIn(dt.date(2026, 1, 18), fasting)


class TrapaveWeeksTestCase(TestCase):
    """Тестови за трапаве седмице (без поста)."""

    def test_bright_week_after_easter(self):
        """Светла седмица: 7 дана после Васкрса."""
        vaskrs = Slava.calc_vaskrs(2026)
        trapave = get_trapave_weeks(2026)
        for i in range(1, 8):
            self.assertIn(vaskrs + dt.timedelta(days=i), trapave)

    def test_post_christmas_trapava(self):
        """После Божића до Крстовдана: 7-17. јануар."""
        trapave = get_trapave_weeks(2026)
        self.assertIn(dt.date(2026, 1, 7), trapave)
        self.assertIn(dt.date(2026, 1, 17), trapave)
        self.assertNotIn(dt.date(2026, 1, 18), trapave)

    def test_wednesday_in_trapava_not_fasting(self):
        """Среда у трапавој седмици није постни дан."""
        vaskrs = Slava.calc_vaskrs(2026)
        # Нађи среду у Светлој седмици
        for i in range(1, 8):
            day = vaskrs + dt.timedelta(days=i)
            if day.weekday() == 2:  # среда
                self.assertFalse(
                    is_fasting_day(day),
                    f"{day} је среда у Светлој седмици, не пости се",
                )
                break


class GetFastingTypeTestCase(TestCase):
    """Тестови за одређивање типа поста."""

    def test_easter_sunday_not_fasting(self):
        """Васкрс није постни дан."""
        vaskrs = Slava.calc_vaskrs(2026)
        result = get_fasting_type(vaskrs)
        self.assertFalse(result["is_fasting"])

    def test_great_lent_weekday_water(self):
        """Радни дан у Великом посту: вода."""
        vaskrs = Slava.calc_vaskrs(2026)
        # Чисти понедељак
        clean_monday = vaskrs - dt.timedelta(days=48)
        result = get_fasting_type(clean_monday)
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "вода")

    def test_great_lent_weekend_oil(self):
        """Субота/недеља у Великом посту: уље."""
        vaskrs = Slava.calc_vaskrs(2026)
        # Нађи прву суботу у Великом посту
        clean_monday = vaskrs - dt.timedelta(days=48)
        first_saturday = clean_monday + dt.timedelta(days=5)
        result = get_fasting_type(first_saturday)
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "уље")

    def test_annunciation_in_lent_fish(self):
        """Благовести (25. март) у Великом посту: риба."""
        # Благовести 2026 пада у Велики пост (Васкрс је 12. април)
        result = get_fasting_type(dt.date(2026, 3, 25))
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "риба")

    def test_palm_sunday_fish(self):
        """Цвети (недеља пре Васкрса): риба."""
        vaskrs = Slava.calc_vaskrs(2026)
        cveti = vaskrs - dt.timedelta(days=7)
        result = get_fasting_type(cveti)
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "риба")

    def test_lazarus_saturday_fish(self):
        """Лазарева субота: риба."""
        vaskrs = Slava.calc_vaskrs(2026)
        lazareva = vaskrs - dt.timedelta(days=8)
        result = get_fasting_type(lazareva)
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "риба")

    def test_cheesefare_beli_mrs(self):
        """Бели мрс: дозвољено све осим меса."""
        vaskrs = Slava.calc_vaskrs(2026)
        cheese_day = vaskrs - dt.timedelta(days=50)
        result = get_fasting_type(cheese_day)
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "бели_мрс")

    def test_christmas_fast_sochi_water(self):
        """Сочи дан (6. јануар): строг пост."""
        result = get_fasting_type(dt.date(2026, 1, 6))
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "вода")

    def test_christmas_day_not_fasting(self):
        """Божић (7. јануар): није пост."""
        result = get_fasting_type(dt.date(2026, 1, 7))
        self.assertFalse(result["is_fasting"])

    def test_dormition_transfiguration_fish(self):
        """Преображење (6. август) у Успенском посту: риба."""
        result = get_fasting_type(dt.date(2026, 8, 6))
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "риба")

    def test_krstovdan_water(self):
        """Крстовдан (18. јануар): строг пост."""
        result = get_fasting_type(dt.date(2026, 1, 18))
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "вода")

    def test_regular_wednesday_fasting(self):
        """Обична среда: пост (вода)."""
        # Нађи среду која није ни у ком посту ни у трапавој седмици
        # Јул 2026: Васкрс је 12. април, тако да је јул безбедан
        # 1. јул 2026 је среда
        result = get_fasting_type(dt.date(2026, 7, 1))
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "вода")

    def test_regular_friday_fasting(self):
        """Обична петак: пост (вода)."""
        result = get_fasting_type(dt.date(2026, 7, 3))
        self.assertTrue(result["is_fasting"])
        self.assertEqual(result["type"], "вода")

    def test_regular_monday_not_fasting(self):
        """Обични понедељак (ван поста): није пост."""
        # Септембар 2026: ван свих постова
        # 7. септембар 2026 је понедељак
        result = get_fasting_type(dt.date(2026, 9, 7))
        self.assertFalse(result["is_fasting"])

    def test_return_dict_structure(self):
        """Повратни речник увек има тачне кључеве."""
        result = get_fasting_type(dt.date(2026, 6, 15))
        self.assertIn("is_fasting", result)
        self.assertIn("type", result)
        self.assertIn("display", result)
        self.assertIn("description", result)


class IsFastingDayTestCase(TestCase):
    """Тестови за is_fasting_day функцију."""

    def test_easter_not_fasting(self):
        """Васкрс није постни дан."""
        vaskrs = Slava.calc_vaskrs(2026)
        self.assertFalse(is_fasting_day(vaskrs))

    def test_great_lent_is_fasting(self):
        """Дан у Великом посту је постни дан."""
        vaskrs = Slava.calc_vaskrs(2026)
        clean_monday = vaskrs - dt.timedelta(days=48)
        self.assertTrue(is_fasting_day(clean_monday))

    def test_regular_thursday_not_fasting(self):
        """Обични четвртак (ван поста): није постни дан."""
        # 10. септембар 2026 је четвртак, ван свих постова
        self.assertFalse(is_fasting_day(dt.date(2026, 9, 10)))

    def test_christmas_fast_is_fasting(self):
        """Дан у Божићном посту је постни дан."""
        self.assertTrue(is_fasting_day(dt.date(2026, 12, 1)))

    def test_dormition_fast_is_fasting(self):
        """Дан у Успенском посту је постни дан."""
        self.assertTrue(is_fasting_day(dt.date(2026, 8, 5)))
