"""
Тестови за функције транслитерације и претраге у utils.py.
"""

from django.test import TestCase
from registar.utils import cyrillic_to_latin, get_query_variants, latin_to_cyrillic


class LatinToCyrillicTestCase(TestCase):
    """Тестови за конверзију латинице у ћирилицу."""

    def test_simple_lowercase(self):
        """Конверзија једноставних малих слова."""
        self.assertEqual(latin_to_cyrillic("beograd"), "београд")

    def test_simple_uppercase(self):
        """Конверзија великих слова."""
        self.assertEqual(latin_to_cyrillic("BEOGRAD"), "БЕОГРАД")

    def test_mixed_case(self):
        """Конверзија мешовитих великих и малих слова."""
        self.assertEqual(latin_to_cyrillic("Beograd"), "Београд")

    def test_digraphs_nj(self):
        """Конверзија диграфа NJ/Nj/nj."""
        self.assertEqual(latin_to_cyrillic("nj"), "њ")
        self.assertEqual(latin_to_cyrillic("Nj"), "Њ")
        self.assertEqual(latin_to_cyrillic("NJ"), "Њ")
        self.assertEqual(latin_to_cyrillic("Njegoš"), "Његош")

    def test_digraphs_lj(self):
        """Конверзија диграфа LJ/Lj/lj."""
        self.assertEqual(latin_to_cyrillic("lj"), "љ")
        self.assertEqual(latin_to_cyrillic("Lj"), "Љ")
        self.assertEqual(latin_to_cyrillic("LJ"), "Љ")
        self.assertEqual(latin_to_cyrillic("Ljubljana"), "Љубљана")

    def test_digraphs_dz(self):
        """Конверзија диграфа DŽ/Dž/dž."""
        self.assertEqual(latin_to_cyrillic("dž"), "џ")
        self.assertEqual(latin_to_cyrillic("Dž"), "Џ")
        self.assertEqual(latin_to_cyrillic("DŽ"), "Џ")

    def test_diacritics(self):
        """Конверзија слова са дијакритицима."""
        self.assertEqual(latin_to_cyrillic("š"), "ш")
        self.assertEqual(latin_to_cyrillic("č"), "ч")
        self.assertEqual(latin_to_cyrillic("ć"), "ћ")
        self.assertEqual(latin_to_cyrillic("ž"), "ж")
        self.assertEqual(latin_to_cyrillic("đ"), "ђ")

    def test_dj_alternative(self):
        """Конверзија DJ као алтернативе за Đ."""
        self.assertEqual(latin_to_cyrillic("dj"), "ђ")
        self.assertEqual(latin_to_cyrillic("Dj"), "Ђ")
        self.assertEqual(latin_to_cyrillic("Djordje"), "Ђорђе")

    def test_full_name(self):
        """Конверзија пуног имена."""
        self.assertEqual(latin_to_cyrillic("Nikola Petrović"), "Никола Петровић")

    def test_empty_string(self):
        """Празан стринг остаје празан."""
        self.assertEqual(latin_to_cyrillic(""), "")

    def test_none_returns_none(self):
        """None вредност остаје None."""
        self.assertIsNone(latin_to_cyrillic(None))

    def test_numbers_preserved(self):
        """Бројеви остају непромењени."""
        self.assertEqual(latin_to_cyrillic("2024"), "2024")

    def test_mixed_with_numbers(self):
        """Мешавина слова и бројева."""
        self.assertEqual(latin_to_cyrillic("Beograd 2024"), "Београд 2024")


class CyrillicToLatinTestCase(TestCase):
    """Тестови за конверзију ћирилице у латиницу."""

    def test_simple_lowercase(self):
        """Конверзија једноставних малих слова."""
        self.assertEqual(cyrillic_to_latin("београд"), "beograd")

    def test_simple_uppercase(self):
        """Конверзија великих слова."""
        self.assertEqual(cyrillic_to_latin("БЕОГРАД"), "BEOGRAD")

    def test_mixed_case(self):
        """Конверзија мешовитих великих и малих слова."""
        self.assertEqual(cyrillic_to_latin("Београд"), "Beograd")

    def test_special_letters(self):
        """Конверзија посебних ћириличних слова."""
        self.assertEqual(cyrillic_to_latin("њ"), "nj")
        self.assertEqual(cyrillic_to_latin("љ"), "lj")
        self.assertEqual(cyrillic_to_latin("џ"), "dž")
        self.assertEqual(cyrillic_to_latin("ш"), "š")
        self.assertEqual(cyrillic_to_latin("ч"), "č")
        self.assertEqual(cyrillic_to_latin("ћ"), "ć")
        self.assertEqual(cyrillic_to_latin("ж"), "ž")
        self.assertEqual(cyrillic_to_latin("ђ"), "đ")

    def test_full_name(self):
        """Конверзија пуног имена."""
        self.assertEqual(cyrillic_to_latin("Никола Петровић"), "Nikola Petrović")

    def test_empty_string(self):
        """Празан стринг остаје празан."""
        self.assertEqual(cyrillic_to_latin(""), "")

    def test_none_returns_none(self):
        """None вредност остаје None."""
        self.assertIsNone(cyrillic_to_latin(None))


class GetQueryVariantsTestCase(TestCase):
    """Тестови за функцију генерисања варијанти претраге."""

    def test_latin_input_generates_cyrillic(self):
        """Латинични унос генерише ћириличну варијанту."""
        variants = get_query_variants("nikola")
        self.assertIn("nikola", variants)
        self.assertIn("никола", variants)

    def test_cyrillic_input_generates_latin(self):
        """Ћирилични унос генерише латиничну варијанту."""
        variants = get_query_variants("никола")
        self.assertIn("никола", variants)
        self.assertIn("nikola", variants)

    def test_empty_string_returns_empty_list(self):
        """Празан стринг враћа празну листу."""
        self.assertEqual(get_query_variants(""), [])

    def test_none_returns_empty_list(self):
        """None вредност враћа празну листу."""
        self.assertEqual(get_query_variants(None), [])

    def test_unique_variants(self):
        """Варијанте су јединствене (без дупликата)."""
        variants = get_query_variants("abc")
        self.assertEqual(len(variants), len(set(variants)))

    def test_complex_name(self):
        """Сложено име генерише обе варијанте."""
        variants = get_query_variants("Đorđević")
        self.assertIn("Đorđević", variants)
        self.assertIn("Ђорђевић", variants)


class RoundTripConversionTestCase(TestCase):
    """Тестови за кружну конверзију латиница → ћирилица → латиница."""

    def test_roundtrip_simple(self):
        """Кружна конверзија једноставног текста."""
        original = "Beograd"
        cyrillic = latin_to_cyrillic(original)
        back_to_latin = cyrillic_to_latin(cyrillic)
        self.assertEqual(back_to_latin, original)

    def test_roundtrip_with_diacritics(self):
        """Кружна конверзија текста са дијакритицима."""
        original = "Petrović"
        cyrillic = latin_to_cyrillic(original)
        back_to_latin = cyrillic_to_latin(cyrillic)
        self.assertEqual(back_to_latin, original)

    def test_roundtrip_cyrillic_start(self):
        """Кружна конверзија почевши од ћирилице."""
        original = "Петровић"
        latin = cyrillic_to_latin(original)
        back_to_cyrillic = latin_to_cyrillic(latin)
        self.assertEqual(back_to_cyrillic, original)
