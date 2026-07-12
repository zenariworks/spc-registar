"""Тестови за парсер вероисповести и народности."""

from django.test import TestCase
from registar.utils_parser import rasclani_vera_narodnost


class ParseVeraNarodnostTest(TestCase):
    """Тестови за parse_vera_narodnost функцију."""

    # --- Празни/None улази ---

    def test_none_input(self):
        """Тест за None улаз."""
        p1, p2 = rasclani_vera_narodnost(None)
        self.assertIsNone(p1["veroispovest"])
        self.assertIsNone(p1["narodnost"])
        self.assertIsNone(p2)

    def test_empty_string(self):
        """Тест за празан стринг."""
        p1, p2 = rasclani_vera_narodnost("")
        self.assertIsNone(p1["veroispovest"])
        self.assertIsNone(p2)

    def test_whitespace_only(self):
        """Тест за стринг са само размацима."""
        p1, p2 = rasclani_vera_narodnost("   ")
        self.assertIsNone(p1["veroispovest"])
        self.assertIsNone(p2)

    # --- Једна особа / оба иста ---

    def test_pravoslavni_srbi(self):
        """Тест за православне Србе."""
        p1, _p2 = rasclani_vera_narodnost("Православни, Срби")
        self.assertEqual(p1["veroispovest"], "Православна")
        self.assertEqual(p1["narodnost"], "Српска")
        self.assertIsNone(_p2)

    def test_pravoslavna(self):
        """Тест за православну."""
        p1, _p2 = rasclani_vera_narodnost("Православна")
        self.assertEqual(p1["veroispovest"], "Православна")
        self.assertIsNone(p1["narodnost"])
        self.assertIsNone(_p2)

    def test_pravoslavna_srbi(self):
        """Тест за православну, Срби."""
        p1, _p2 = rasclani_vera_narodnost("Православна, Срби")
        self.assertEqual(p1["veroispovest"], "Православна")
        self.assertEqual(p1["narodnost"], "Српска")

    def test_rimokatolici(self):
        """Тест за римокатолике."""
        p1, _p2 = rasclani_vera_narodnost("Римокатолици")
        self.assertEqual(p1["veroispovest"], "Римокатоличка")
        self.assertIsNone(p1["narodnost"])

    def test_muslimani(self):
        """Тест за муслимане."""
        p1, _p2 = rasclani_vera_narodnost("Муслимани")
        self.assertEqual(p1["veroispovest"], "Ислам")
        self.assertIsNone(p1["narodnost"])

    def test_protestanti(self):
        """Тест за протестанте."""
        p1, _p2 = rasclani_vera_narodnost("Протестанти")
        self.assertEqual(p1["veroispovest"], "Протестантска")
        self.assertIsNone(p1["narodnost"])

    def test_hriscanin(self):
        """Тест за хришћане."""
        p1, _p2 = rasclani_vera_narodnost("Хришћани")
        self.assertEqual(p1["veroispovest"], "Хришћанска")

    def test_pravoslavni_typo(self):
        """Тест за грешку у куцању 'праволавн'."""
        p1, _p2 = rasclani_vera_narodnost("Праволавни")
        self.assertEqual(p1["veroispovest"], "Православна")

    # --- Два лица ---

    def test_two_persons_orthodox_and_catholic(self):
        """Тест за два лица: православни и римокатолкиња."""
        p1, p2 = rasclani_vera_narodnost("Православни Србин и Римокатолкиња")
        self.assertEqual(p1["veroispovest"], "Православна")
        self.assertEqual(p1["narodnost"], "Српска")
        self.assertIsNotNone(p2)
        self.assertEqual(p2["veroispovest"], "Римокатоличка")
        self.assertIsNone(p2["narodnost"])

    def test_muslim_and_orthodox(self):
        """Тест за муслимана и православну Српкињу."""
        p1, p2 = rasclani_vera_narodnost("Муслиман и Православна Српкиња")
        self.assertEqual(p1["veroispovest"], "Ислам")
        self.assertIsNone(p1["narodnost"])
        self.assertIsNotNone(p2)
        self.assertEqual(p2["veroispovest"], "Православна")
        self.assertEqual(p2["narodnost"], "Српска")

    def test_orthodox_serb_and_hungarian_catholic(self):
        """Тест за православног Србина и Мађарицу Римокатолкињу."""
        p1, p2 = rasclani_vera_narodnost("Православни Србин и Мађарица Римокатолкиња")
        self.assertEqual(p1["veroispovest"], "Православна")
        self.assertEqual(p1["narodnost"], "Српска")
        self.assertIsNotNone(p2)
        self.assertEqual(p2["veroispovest"], "Римокатоличка")
        self.assertEqual(p2["narodnost"], "Мађарска")

    # --- Непознати обрасци ---

    def test_unknown_returns_none(self):
        """Тест да непознати образац враћа None."""
        p1, p2 = rasclani_vera_narodnost("Нешто непознато")
        self.assertIsNone(p1["veroispovest"])
        self.assertIsNone(p1["narodnost"])
        self.assertIsNone(p2)

    # --- Различите народности ---

    def test_madjarska(self):
        """Тест за мађарску народност."""
        p1, _p2 = rasclani_vera_narodnost("Мађар")
        self.assertEqual(p1["narodnost"], "Мађарска")

    def test_srpska_feminine(self):
        """Тест за женски облик српске народности."""
        p1, _p2 = rasclani_vera_narodnost("Српкиња")
        self.assertEqual(p1["narodnost"], "Српска")

    def test_nemacka(self):
        """Тест за немачку народност."""
        p1, _p2 = rasclani_vera_narodnost("Немкиња")
        self.assertEqual(p1["narodnost"], "Немачка")

    def test_romska(self):
        """Тест за ромску народност."""
        p1, _p2 = rasclani_vera_narodnost("Ром")
        self.assertEqual(p1["narodnost"], "Ромска")

    # --- Гркокатоличка ---

    def test_grkokatolik(self):
        """Тест за гркокатолике."""
        p1, _p2 = rasclani_vera_narodnost("Гркокатолик")
        self.assertEqual(p1["veroispovest"], "Гркокатоличка")

    # --- Абревијације ---

    def test_pravo_abbreviation(self):
        """Тест за абревијацију 'прав.'."""
        p1, _p2 = rasclani_vera_narodnost("прав.")
        self.assertEqual(p1["veroispovest"], "Православна")

    def test_case_insensitive(self):
        """Тест за case-insensitive претрагу."""
        p1, _p2 = rasclani_vera_narodnost("православни")
        self.assertEqual(p1["veroispovest"], "Православна")
