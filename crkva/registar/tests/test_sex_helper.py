"""Unit tests for the sex inference helpers."""

from django.test import SimpleTestCase
from registar.migracija.sex import (
    _FEMALE_NAMES,
    _MALE_NAMES,
    FEMALE,
    MALE,
    infer_sex,
    infer_sex_from_role,
    pol_prema_imenu,
)


class SexDictionariesAreDisjoint(SimpleTestCase):
    def test_female_and_male_name_sets_have_no_overlap(self):
        overlap = _FEMALE_NAMES & _MALE_NAMES
        self.assertSetEqual(
            overlap,
            set(),
            msg=(
                f"Names appear in both _FEMALE_NAMES and _MALE_NAMES: {sorted(overlap)}. "
                f"When a name is in both sets, infer_sex_from_name returns None because "
                f"len(hits) != 1. Decide a canonical sex for each duplicate and remove "
                f"from the other set."
            ),
        )


class InferSexFromName(SimpleTestCase):
    def test_unambiguous_male_names(self):
        for n in ["Марко", "Иван", "Лука", "Матија", "Немања", "marko"]:
            self.assertEqual(pol_prema_imenu(n), MALE, msg=n)

    def test_unambiguous_female_names(self):
        for n in ["Ана", "Јелена", "Сања", "Цана", "Марија", "ana"]:
            self.assertEqual(pol_prema_imenu(n), FEMALE, msg=n)

    def test_empty_or_unknown_returns_none(self):
        for n in [None, "", "   ", "Xyzzy"]:
            self.assertIsNone(pol_prema_imenu(n))

    def test_composite_name_uses_first_token(self):
        self.assertEqual(pol_prema_imenu("Марко Петар"), MALE)
        self.assertEqual(pol_prema_imenu("Ана Марија"), FEMALE)


class InferSexFromRole(SimpleTestCase):
    def test_female_roles(self):
        for r in ["мајка", "кћи", "баба", "сестра", "кума"]:
            self.assertEqual(infer_sex_from_role(r), FEMALE, msg=r)

    def test_male_roles(self):
        for r in ["отац", "син", "деда", "брат", "кум"]:
            self.assertEqual(infer_sex_from_role(r), MALE, msg=r)

    def test_unknown_role_returns_none(self):
        self.assertIsNone(infer_sex_from_role("пријатељ"))
        self.assertIsNone(infer_sex_from_role(""))
        self.assertIsNone(infer_sex_from_role(None))


class InferSexCombined(SimpleTestCase):
    def test_role_takes_priority_over_name(self):
        # Role wins even if name is unknown
        self.assertEqual(infer_sex(ime="Xyzzy", uloga="мајка"), FEMALE)
        # Name fallback when no role
        self.assertEqual(infer_sex(ime="Марко", uloga=None), MALE)
