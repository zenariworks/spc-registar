"""
Тестови за функције пресловљавања и претраге у registar.utils.
"""

from django.test import TestCase
from registar.utils import get_query_variants, preslovljavanje


class LatinToCyrillicTestCase(TestCase):
    """Тестови за пресловљавање латинице у ћирилицу (u="cir")."""

    def test_simple_lowercase(self):
        """Пресловљавање једноставних малих слова."""
        self.assertEqual(preslovljavanje("beograd"), "београд")

    def test_simple_uppercase(self):
        """Пресловљавање великих слова."""
        self.assertEqual(preslovljavanje("BEOGRAD"), "БЕОГРАД")

    def test_mixed_case(self):
        """Пресловљавање мешовитих великих и малих слова."""
        self.assertEqual(preslovljavanje("Beograd"), "Београд")

    def test_digraphs_nj(self):
        """Пресловљавање диграфа NJ/Nj/nj."""
        self.assertEqual(preslovljavanje("nj"), "њ")
        self.assertEqual(preslovljavanje("Nj"), "Њ")
        self.assertEqual(preslovljavanje("NJ"), "Њ")
        self.assertEqual(preslovljavanje("Njegoš"), "Његош")

    def test_digraphs_lj(self):
        """Пресловљавање диграфа LJ/Lj/lj."""
        self.assertEqual(preslovljavanje("lj"), "љ")
        self.assertEqual(preslovljavanje("Lj"), "Љ")
        self.assertEqual(preslovljavanje("LJ"), "Љ")
        self.assertEqual(preslovljavanje("Ljubljana"), "Љубљана")

    def test_digraphs_dz(self):
        """Пресловљавање диграфа DŽ/Dž/dž."""
        self.assertEqual(preslovljavanje("dž"), "џ")
        self.assertEqual(preslovljavanje("Dž"), "Џ")
        self.assertEqual(preslovljavanje("DŽ"), "Џ")

    def test_diacritics(self):
        """Пресловљавање слова са дијакритицима."""
        self.assertEqual(preslovljavanje("š"), "ш")
        self.assertEqual(preslovljavanje("č"), "ч")
        self.assertEqual(preslovljavanje("ć"), "ћ")
        self.assertEqual(preslovljavanje("ž"), "ж")
        self.assertEqual(preslovljavanje("đ"), "ђ")

    def test_dj_alternative(self):
        """Пресловљавање DJ као алтернативе за Đ."""
        self.assertEqual(preslovljavanje("dj"), "ђ")
        self.assertEqual(preslovljavanje("Dj"), "Ђ")
        self.assertEqual(preslovljavanje("Djordje"), "Ђорђе")

    def test_full_name(self):
        """Пресловљавање пуног имена."""
        self.assertEqual(preslovljavanje("Nikola Petrović"), "Никола Петровић")

    def test_empty_string(self):
        """Празан стринг остаје празан."""
        self.assertEqual(preslovljavanje(""), "")

    def test_none_returns_empty(self):
        """None вредност се враћа као "" (миграција очекује стринг)."""
        self.assertEqual(preslovljavanje(None), "")

    def test_numbers_preserved(self):
        """Бројеви остају непромењени."""
        self.assertEqual(preslovljavanje("2024"), "2024")

    def test_mixed_with_numbers(self):
        """Мешавина слова и бројева."""
        self.assertEqual(preslovljavanje("Beograd 2024"), "Београд 2024")


class CyrillicToLatinTestCase(TestCase):
    """Тестови за пресловљавање ћирилице у латиницу (u="lat")."""

    def test_simple_lowercase(self):
        """Пресловљавање једноставних малих слова."""
        self.assertEqual(preslovljavanje("београд", u="lat"), "beograd")

    def test_simple_uppercase(self):
        """Пресловљавање великих слова."""
        self.assertEqual(preslovljavanje("БЕОГРАД", u="lat"), "BEOGRAD")

    def test_mixed_case(self):
        """Пресловљавање мешовитих великих и малих слова."""
        self.assertEqual(preslovljavanje("Београд", u="lat"), "Beograd")

    def test_special_letters(self):
        """Пресловљавање посебних ћириличних слова."""
        self.assertEqual(preslovljavanje("њ", u="lat"), "nj")
        self.assertEqual(preslovljavanje("љ", u="lat"), "lj")
        self.assertEqual(preslovljavanje("џ", u="lat"), "dž")
        self.assertEqual(preslovljavanje("ш", u="lat"), "š")
        self.assertEqual(preslovljavanje("ч", u="lat"), "č")
        self.assertEqual(preslovljavanje("ћ", u="lat"), "ć")
        self.assertEqual(preslovljavanje("ж", u="lat"), "ž")
        self.assertEqual(preslovljavanje("ђ", u="lat"), "đ")

    def test_full_name(self):
        """Пресловљавање пуног имена."""
        self.assertEqual(preslovljavanje("Никола Петровић", u="lat"), "Nikola Petrović")

    def test_empty_string(self):
        """Празан стринг остаје празан."""
        self.assertEqual(preslovljavanje("", u="lat"), "")

    def test_none_returns_empty(self):
        """None вредност се враћа као ""."""
        self.assertEqual(preslovljavanje(None, u="lat"), "")


class NepoznatSmerTestCase(TestCase):
    """Непознат смер подиже ValueError."""

    def test_invalid_direction_raises(self):
        with self.assertRaises(ValueError):
            preslovljavanje("beograd", u="xx")


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
    """Тестови за кружно пресловљавање латиница → ћирилица → латиница."""

    def test_roundtrip_simple(self):
        """Кружно пресловљавање једноставног текста."""
        original = "Beograd"
        cyrillic = preslovljavanje(original)
        back_to_latin = preslovljavanje(cyrillic, u="lat")
        self.assertEqual(back_to_latin, original)

    def test_roundtrip_with_diacritics(self):
        """Кружно пресловљавање текста са дијакритицима."""
        original = "Petrović"
        cyrillic = preslovljavanje(original)
        back_to_latin = preslovljavanje(cyrillic, u="lat")
        self.assertEqual(back_to_latin, original)

    def test_roundtrip_cyrillic_start(self):
        """Кружно пресловљавање почевши од ћирилице."""
        original = "Петровић"
        latin = preslovljavanje(original, u="lat")
        back_to_cyrillic = preslovljavanje(latin)
        self.assertEqual(back_to_cyrillic, original)
