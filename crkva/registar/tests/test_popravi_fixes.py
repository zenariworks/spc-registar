"""#354: popravi_devojacka уклоњен из importuj_dbf пајплајна.

Увоз већ скида маркере девојачког презимена (extract_maiden/ocisti_prezime у
свакој migracija_* путањи), па је накнадна поправка no-op на исправном увозу.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.test import TestCase
from registar.management.commands.importuj_dbf import PIPELINE


class ImportujPipelineTests(TestCase):
    def test_popravi_devojacka_not_in_pipeline(self):
        ids = [s[0] for s in PIPELINE]
        self.assertNotIn("popravi_devojacka", ids)
        self.assertIn("popravi_duplikate", ids)
        self.assertIn("migracija_krstenja", ids)


class VencanjaMaidenStripTests(TestCase):
    def test_parse_person_strips_maiden_marker(self):
        from registar.uvoz.migracija_vencanja import Command as MigracijaVencanja

        cmd = MigracijaVencanja()
        cmd._verbose = False
        osoba = cmd._parse_person("Мара р.Алексић", label="свекрва")
        self.assertEqual(osoba.prezime, "Алексић")
        self.assertEqual(osoba.devojacko_prezime, "Алексић")
