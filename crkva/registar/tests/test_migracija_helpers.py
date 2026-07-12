"""Tests for the migracija helpers package (pure functions, no DB)."""

# pylint: disable=missing-function-docstring,missing-class-docstring,attribute-defined-outside-init,too-many-locals,broad-exception-caught,not-callable

from datetime import date, time

from django.test import TestCase
from registar.utils.migracija.cache import normalise_hram_naziv, normalise_zanimanje
from registar.utils.migracija.errors import RecordContext, RecordSkipped
from registar.utils.migracija.helpers import (
    cirilica,
    cirilica_int,
    ocisti_prezime,
    podeli_zadnju_rec,
    rasclani_puno_ime,
    rasclani_vreme,
    siguran_datum,
)


class OcistiPrezimeTests(TestCase):
    def test_preserves_leading_R_when_no_marker(self):
        # Regression: the old regex was eating leading Р/R.
        self.assertEqual(ocisti_prezime("Радановић"), "Радановић")
        self.assertEqual(ocisti_prezime("Радивојевић"), "Радивојевић")
        self.assertEqual(ocisti_prezime("Ристић"), "Ристић")
        self.assertEqual(ocisti_prezime("Radanović"), "Radanović")

    def test_strips_cyrillic_marker_with_period(self):
        self.assertEqual(ocisti_prezime("р.Јовановић"), "Јовановић")
        self.assertEqual(ocisti_prezime("р. Јовановић"), "Јовановић")
        self.assertEqual(ocisti_prezime("Р.Јовановић"), "Јовановић")

    def test_strips_cyrillic_marker_with_space(self):
        self.assertEqual(ocisti_prezime("р Марковић"), "Марковић")
        self.assertEqual(ocisti_prezime("Р Марковић"), "Марковић")

    def test_strips_latin_marker(self):
        self.assertEqual(ocisti_prezime("r.Marković"), "Marković")
        self.assertEqual(ocisti_prezime("R. Marković"), "Marković")
        self.assertEqual(ocisti_prezime("r markovic"), "Markovic")

    def test_strips_rodjena(self):
        self.assertEqual(ocisti_prezime("рођена Ђорђевић"), "Ђорђевић")
        self.assertEqual(ocisti_prezime("Рођена Ђорђевић"), "Ђорђевић")

    def test_capitalises_lowercase_first_letter(self):
        self.assertEqual(ocisti_prezime("томић"), "Томић")
        self.assertEqual(ocisti_prezime("филиповић"), "Филиповић")

    def test_handles_empty(self):
        self.assertEqual(ocisti_prezime(""), "")
        self.assertEqual(ocisti_prezime(None), "")


class SplitFullNameTests(TestCase):
    def test_simple_split(self):
        self.assertEqual(rasclani_puno_ime("Марко Петровић"), ("Марко", "Петровић"))

    def test_camelcase_split(self):
        self.assertEqual(rasclani_puno_ime("МаркоПетровић"), ("Марко", "Петровић"))

    def test_no_split_possible(self):
        self.assertEqual(rasclani_puno_ime("Марко"), (None, None))

    def test_empty_input(self):
        self.assertEqual(rasclani_puno_ime(""), (None, None))
        self.assertEqual(rasclani_puno_ime(None), (None, None))

    def test_strips_whitespace(self):
        self.assertEqual(rasclani_puno_ime("  Марко Петровић  "), ("Марко", "Петровић"))


class SplitFullNameLastWordTests(TestCase):
    def test_two_words(self):
        self.assertEqual(podeli_zadnju_rec("Марко Петровић"), ("Марко", "Петровић"))

    def test_three_words_keeps_last_as_prezime(self):
        self.assertEqual(
            podeli_zadnju_rec("Петар Никола Петровић"),
            ("Петар Никола", "Петровић"),
        )

    def test_single_word(self):
        self.assertEqual(podeli_zadnju_rec("Марко"), ("Марко", ""))


class SafeDateTests(TestCase):
    def test_valid_date(self):
        self.assertEqual(siguran_datum(2020, 5, 14), date(2020, 5, 14))

    def test_rejects_pre_1900(self):
        self.assertIsNone(siguran_datum(0, 1, 1))
        self.assertIsNone(siguran_datum(1899, 12, 31))

    def test_fills_in_default_month_day_when_zero(self):
        self.assertEqual(siguran_datum(2020, 0, 0), date(2020, 1, 1))

    def test_invalid_returns_none(self):
        self.assertIsNone(siguran_datum(2020, 2, 30))
        self.assertIsNone(siguran_datum(2020, 13, 1))


class ParseTimeTests(TestCase):
    def test_simple_hour(self):
        self.assertEqual(rasclani_vreme("14"), time(14, 0))

    def test_dot_separator(self):
        self.assertEqual(rasclani_vreme("14.30"), time(14, 30))

    def test_comma_separator(self):
        self.assertEqual(rasclani_vreme("14,30"), time(14, 30))

    def test_normalises_24_to_0(self):
        self.assertEqual(rasclani_vreme("24"), time(0, 0))

    def test_clamps_out_of_range(self):
        self.assertEqual(rasclani_vreme("99.99"), time(23, 59))

    def test_empty_returns_none(self):
        self.assertIsNone(rasclani_vreme(""))
        self.assertIsNone(rasclani_vreme(None))

    def test_garbage_returns_none(self):
        self.assertIsNone(rasclani_vreme("nope"))


class CyrTests(TestCase):
    def test_latin_to_cyrillic_via_yuscii(self):
        # } maps to ћ in the YUSCII source encoding
        self.assertEqual(cirilica("Radanovi}"), "Радановић")
        self.assertEqual(cirilica("Mihailovi}"), "Михаиловић")

    def test_strips_whitespace(self):
        self.assertEqual(cirilica("  Marko  "), "Марко")

    def test_handles_none(self):
        self.assertEqual(cirilica(None), "")


class CyrIntTests(TestCase):
    def test_valid_int(self):
        self.assertEqual(cirilica_int("42"), 42)

    def test_invalid_returns_default(self):
        self.assertEqual(cirilica_int("nope", podrazumevano=7), 7)


class HramNormaliserTests(TestCase):
    def test_strips_literal_hram(self):
        self.assertEqual(normalise_hram_naziv("hram Светог Саве"), "Светог Саве")
        self.assertEqual(normalise_hram_naziv("Hram Светог Саве"), "Светог Саве")
        self.assertEqual(normalise_hram_naziv("храм Светог Саве"), "Светог Саве")

    def test_keeps_clean_naziv(self):
        self.assertEqual(normalise_hram_naziv("Светог Саве"), "Светог Саве")

    def test_empty_falls_back(self):
        self.assertEqual(normalise_hram_naziv(""), "Непознат храм")
        self.assertEqual(normalise_hram_naziv(None), "Непознат храм")


class ZanimanjeNormaliserTests(TestCase):
    def test_lowercases(self):
        self.assertEqual(normalise_zanimanje("Учитељ"), "учитељ")
        self.assertEqual(normalise_zanimanje("УЧИТЕЉ"), "учитељ")


class RecordContextTests(TestCase):
    def test_stringifies_with_all_fields(self):
        ctx = RecordContext(
            table="hsp_vencanja",
            redni_broj=42,
            godina=2024,
            knjiga="1",
            strana="72",
            broj="4",
        )
        s = str(ctx)
        self.assertIn("hsp_vencanja", s)
        self.assertIn("#42", s)
        self.assertIn("2024.", s)
        self.assertIn("књ.1", s)

    def test_record_skipped_carries_context(self):
        ctx = RecordContext(table="hsp_x", redni_broj=1)
        exc = RecordSkipped(ctx, "incomplete name")
        self.assertEqual(exc.ctx, ctx)
        self.assertEqual(exc.reason, "incomplete name")
