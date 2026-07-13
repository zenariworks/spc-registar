"""
Unit tests for migration converter utilities.
Tests the Konvertor class used in data migration from legacy DBF files.
"""

from datetime import date

from django.test import SimpleTestCase
from registar.utils.preslovljavanje import Konvertor, preslovljavanje


class TestKonvertor(SimpleTestCase):
    """Test suite for the Konvertor utility class."""

    # ===== preslovljavanje() tests =====

    def test_string_latin_to_cyrillic_simple(self):
        """Latin 'Beograd' converts to Cyrillic 'Београд'."""
        self.assertEqual(preslovljavanje("Beograd"), "Београд")

    def test_string_latin_to_cyrillic_uppercase(self):
        """Uppercase Latin 'BEOGRAD' converts to uppercase Cyrillic 'БЕОГРАД'."""
        self.assertEqual(preslovljavanje("BEOGRAD"), "БЕОГРАД")

    def test_string_special_serbian_chars_cacak(self):
        """Special Serbian Latin 'Čačak' converts to 'Чачак'."""
        self.assertEqual(preslovljavanje("Čačak"), "Чачак")

    def test_string_special_serbian_chars_sabac(self):
        """Special Serbian Latin 'Šabac' converts to 'Шабац'."""
        self.assertEqual(preslovljavanje("Šabac"), "Шабац")

    def test_string_special_serbian_chars_zabalj(self):
        """Serbian Latin 'Žabalj' converts to 'Жабаљ' (lj is one digraph, #339)."""
        self.assertEqual(preslovljavanje("Žabalj"), "Жабаљ")

    def test_string_cirilica_cd_letters(self):
        """Ć/ć and Đ/đ transliterate to Ћ/ћ and Ђ/ђ (#339)."""
        self.assertEqual(preslovljavanje("Ćuković"), "Ћуковић")
        self.assertEqual(preslovljavanje("Đorđe"), "Ђорђе")
        self.assertEqual(preslovljavanje("ćup"), "ћуп")
        self.assertEqual(preslovljavanje("među"), "међу")

    def test_string_digraphs_lj_nj_dz(self):
        """Latin digraphs Lj/Nj/Dž (any case) map to single љ/њ/џ (#339)."""
        self.assertEqual(preslovljavanje("Ljubomir"), "Љубомир")
        self.assertEqual(preslovljavanje("konj"), "коњ")
        self.assertEqual(preslovljavanje("Njegoš"), "Његош")
        self.assertEqual(preslovljavanje("džak"), "џак")
        self.assertEqual(preslovljavanje("NJEGOŠ"), "ЊЕГОШ")
        self.assertEqual(preslovljavanje("LJUBA"), "ЉУБА")

    def test_string_legacy_hramsp_encoding_q(self):
        """Legacy HramSP encoding 'q' converts to 'љ'."""
        self.assertEqual(preslovljavanje("q"), "љ")

    def test_string_legacy_hramsp_encoding_w(self):
        """Legacy HramSP encoding 'w' converts to 'њ'."""
        self.assertEqual(preslovljavanje("w"), "њ")

    def test_string_legacy_hramsp_encoding_bracket(self):
        """Legacy HramSP encoding ']' converts to 'Ћ'."""
        self.assertEqual(preslovljavanje("]"), "Ћ")

    def test_string_legacy_hramsp_encoding_brace(self):
        """Legacy HramSP encoding '}' converts to 'ћ'."""
        self.assertEqual(preslovljavanje("}"), "ћ")

    def test_string_legacy_hramsp_encoding_backslash(self):
        """Legacy HramSP encoding '\\' converts to 'Ђ'."""
        self.assertEqual(preslovljavanje("\\"), "Ђ")

    def test_string_legacy_hramsp_encoding_pipe(self):
        """Legacy HramSP encoding '|' converts to 'ђ'."""
        self.assertEqual(preslovljavanje("|"), "ђ")

    def test_string_legacy_hramsp_encoding_x(self):
        """Legacy HramSP encoding 'x' converts to 'џ'."""
        self.assertEqual(preslovljavanje("x"), "џ")

    def test_string_empty_returns_empty(self):
        """Empty string returns empty string."""
        self.assertEqual(preslovljavanje(""), "")

    def test_string_whitespace_only_returns_empty(self):
        """Whitespace-only string returns empty string."""
        self.assertEqual(preslovljavanje("   "), "")

    def test_string_already_cyrillic_unchanged(self):
        """Already-Cyrillic text passes through unchanged."""
        self.assertEqual(preslovljavanje("Београд"), "Београд")

    # ===== Konvertor.int() tests =====

    def test_int_valid_string(self):
        """Valid numeric string '123' converts to integer 123."""
        self.assertEqual(Konvertor.int("123"), 123)

    def test_int_empty_string_default(self):
        """Empty string returns default value 0."""
        self.assertEqual(Konvertor.int(""), 0)

    def test_int_none_default(self):
        """None returns default value 0."""
        self.assertEqual(Konvertor.int(None), 0)

    def test_int_non_numeric_default(self):
        """Non-numeric string 'abc' returns default value 0."""
        self.assertEqual(Konvertor.int("abc"), 0)

    def test_int_custom_default(self):
        """Non-numeric string with custom default -1 returns -1."""
        self.assertEqual(Konvertor.int("abc", default=-1), -1)

    def test_int_float_string_default(self):
        """Float string '12.5' returns default (no truncation expected)."""
        self.assertEqual(Konvertor.int("12.5"), 0)

    # ===== Konvertor.date() tests =====

    def test_date_normal(self):
        """Normal date (2000, 3, 15) returns date(2000, 3, 15)."""
        self.assertEqual(Konvertor.datum(2000, 3, 15), date(2000, 3, 15))

    def test_date_zero_year(self):
        """Zero year (0, 3, 15) returns date(1900, 3, 15)."""
        self.assertEqual(Konvertor.datum(0, 3, 15), date(1900, 3, 15))

    def test_date_zero_month(self):
        """Zero month (2000, 0, 15) returns date(2000, 1, 15)."""
        self.assertEqual(Konvertor.datum(2000, 0, 15), date(2000, 1, 15))

    def test_date_zero_day(self):
        """Zero day (2000, 3, 0) returns date(2000, 3, 1)."""
        self.assertEqual(Konvertor.datum(2000, 3, 0), date(2000, 3, 1))

    def test_date_all_zeros(self):
        """All zeros (0, 0, 0) returns date(1900, 1, 1)."""
        self.assertEqual(Konvertor.datum(0, 0, 0), date(1900, 1, 1))

    def test_date_none_values(self):
        """None values return date(1900, 1, 1)."""
        self.assertEqual(Konvertor.datum(None, None, None), date(1900, 1, 1))

    # ===== Konvertor.split_name() tests =====

    def test_split_name_with_space(self):
        """'Петар Петровић' splits to ('Петар', 'Петровић')."""
        self.assertEqual(Konvertor.split_name("Петар Петровић"), ("Петар", "Петровић"))

    def test_split_name_camelcase_cyrillic(self):
        """'СлавицаЋуковић' (no space, camelCase) splits to ('Славица', 'Ћуковић')."""
        self.assertEqual(Konvertor.split_name("СлавицаЋуковић"), ("Славица", "Ћуковић"))

    def test_split_name_empty_string(self):
        """Empty string returns (None, None)."""
        self.assertEqual(Konvertor.split_name(""), (None, None))

    def test_split_name_none(self):
        """None returns (None, None)."""
        self.assertEqual(Konvertor.split_name(None), (None, None))

    def test_split_name_single_word(self):
        """Single word 'Петар' returns (None, None)."""
        self.assertEqual(Konvertor.split_name("Петар"), (None, None))
