"""
Unit tests for migration converter utilities.
Tests preslovi/u_int/rasclani_puno_ime used in legacy DBF migration.
"""

from django.test import SimpleTestCase
from registar.utils.migracija.helpers import rasclani_puno_ime, u_int
from registar.utils.preslovljavanje import preslovi


class TestKonvertor(SimpleTestCase):
    """Test suite for migration converter helpers."""

    # ===== preslovi() tests =====

    def test_string_latin_to_cyrillic_simple(self):
        """Latin 'Beograd' converts to Cyrillic 'Београд'."""
        self.assertEqual(preslovi("Beograd"), "Београд")

    def test_string_latin_to_cyrillic_uppercase(self):
        """Uppercase Latin 'BEOGRAD' converts to uppercase Cyrillic 'БЕОГРАД'."""
        self.assertEqual(preslovi("BEOGRAD"), "БЕОГРАД")

    def test_string_special_serbian_chars_cacak(self):
        """Special Serbian Latin 'Čačak' converts to 'Чачак'."""
        self.assertEqual(preslovi("Čačak"), "Чачак")

    def test_string_special_serbian_chars_sabac(self):
        """Special Serbian Latin 'Šabac' converts to 'Шабац'."""
        self.assertEqual(preslovi("Šabac"), "Шабац")

    def test_string_special_serbian_chars_zabalj(self):
        """Serbian Latin 'Žabalj' converts to 'Жабаљ' (lj is one digraph, #339)."""
        self.assertEqual(preslovi("Žabalj"), "Жабаљ")

    def test_string_cirilica_cd_letters(self):
        """Ć/ć and Đ/đ transliterate to Ћ/ћ and Ђ/ђ (#339)."""
        self.assertEqual(preslovi("Ćuković"), "Ћуковић")
        self.assertEqual(preslovi("Đorđe"), "Ђорђе")
        self.assertEqual(preslovi("ćup"), "ћуп")
        self.assertEqual(preslovi("među"), "међу")

    def test_string_digraphs_lj_nj_dz(self):
        """Latin digraphs Lj/Nj/Dž (any case) map to single љ/њ/џ (#339)."""
        self.assertEqual(preslovi("Ljubomir"), "Љубомир")
        self.assertEqual(preslovi("konj"), "коњ")
        self.assertEqual(preslovi("Njegoš"), "Његош")
        self.assertEqual(preslovi("džak"), "џак")
        self.assertEqual(preslovi("NJEGOŠ"), "ЊЕГОШ")
        self.assertEqual(preslovi("LJUBA"), "ЉУБА")

    def test_string_legacy_hramsp_encoding_q(self):
        """Legacy HramSP encoding 'q' converts to 'љ'."""
        self.assertEqual(preslovi("q"), "љ")

    def test_string_legacy_hramsp_encoding_w(self):
        """Legacy HramSP encoding 'w' converts to 'њ'."""
        self.assertEqual(preslovi("w"), "њ")

    def test_string_legacy_hramsp_encoding_bracket(self):
        """Legacy HramSP encoding ']' converts to 'Ћ'."""
        self.assertEqual(preslovi("]"), "Ћ")

    def test_string_legacy_hramsp_encoding_brace(self):
        """Legacy HramSP encoding '}' converts to 'ћ'."""
        self.assertEqual(preslovi("}"), "ћ")

    def test_string_legacy_hramsp_encoding_backslash(self):
        """Legacy HramSP encoding '\\' converts to 'Ђ'."""
        self.assertEqual(preslovi("\\"), "Ђ")

    def test_string_legacy_hramsp_encoding_pipe(self):
        """Legacy HramSP encoding '|' converts to 'ђ'."""
        self.assertEqual(preslovi("|"), "ђ")

    def test_string_legacy_hramsp_encoding_x(self):
        """Legacy HramSP encoding 'x' converts to 'џ'."""
        self.assertEqual(preslovi("x"), "џ")

    def test_string_empty_returns_empty(self):
        """Empty string returns empty string."""
        self.assertEqual(preslovi(""), "")

    def test_string_whitespace_only_returns_empty(self):
        """Whitespace-only string returns empty string."""
        self.assertEqual(preslovi("   "), "")

    def test_string_already_cyrillic_unchanged(self):
        """Already-Cyrillic text passes through unchanged."""
        self.assertEqual(preslovi("Београд"), "Београд")

    # ===== u_int() tests =====

    def test_int_valid_string(self):
        """Valid numeric string '123' converts to integer 123."""
        self.assertEqual(u_int("123"), 123)

    def test_int_empty_string_default(self):
        """Empty string returns default value 0."""
        self.assertEqual(u_int(""), 0)

    def test_int_none_default(self):
        """None returns default value 0."""
        self.assertEqual(u_int(None), 0)

    def test_int_non_numeric_default(self):
        """Non-numeric string 'abc' returns default value 0."""
        self.assertEqual(u_int("abc"), 0)

    def test_int_custom_default(self):
        """Non-numeric string with custom default -1 returns -1."""
        self.assertEqual(u_int("abc", -1), -1)

    def test_int_float_string_default(self):
        """Float string '12.5' returns default (no truncation expected)."""
        self.assertEqual(u_int("12.5"), 0)

    # ===== rasclani_puno_ime() tests =====

    def test_split_name_with_space(self):
        """'Петар Петровић' splits to ('Петар', 'Петровић')."""
        self.assertEqual(rasclani_puno_ime("Петар Петровић"), ("Петар", "Петровић"))

    def test_split_name_camelcase_cyrillic(self):
        """'СлавицаЋуковић' (no space, camelCase) splits to ('Славица', 'Ћуковић')."""
        self.assertEqual(rasclani_puno_ime("СлавицаЋуковић"), ("Славица", "Ћуковић"))

    def test_split_name_empty_string(self):
        """Empty string returns (None, None)."""
        self.assertEqual(rasclani_puno_ime(""), (None, None))

    def test_split_name_none(self):
        """None returns (None, None)."""
        self.assertEqual(rasclani_puno_ime(None), (None, None))

    def test_split_name_single_word(self):
        """Single word 'Петар' returns (None, None)."""
        self.assertEqual(rasclani_puno_ime("Петар"), (None, None))
