"""#254: K_REGKADA (датум регистрације крштења) је празан у целом извору.

DBF поље ``K_REGKADA`` ('D', 8) је NULL у свих 3579 редова, а ``parse_row`` је
тврдо постављао ``registracija_datum=None`` поред мртвог селекта. Уклоњено из
``SOURCE_COLUMNS`` уз померање ``K_REGBROJ``/``K_REGSTR`` на индексе 46/47.
"""

# pylint: disable=missing-function-docstring

from django.test import SimpleTestCase
from registar.management.commands.migracija_krstenja import SOURCE_COLUMNS, parse_row


class RegKadaRemovedTests(SimpleTestCase):
    def test_regkada_not_in_source_columns(self):
        self.assertNotIn("K_REGKADA", SOURCE_COLUMNS)

    def test_registration_block_is_mesto_broj_strana(self):
        self.assertEqual(SOURCE_COLUMNS[-3:], ("K_REGMESTO", "K_REGBROJ", "K_REGSTR"))

    def test_parse_row_reads_reindexed_registration_columns(self):
        row = [""] * len(SOURCE_COLUMNS)
        row[45] = "100"  # K_REGMESTO
        row[46] = "200"  # K_REGBROJ (раније 47)
        row[47] = "300"  # K_REGSTR  (раније 48)
        rec = parse_row(tuple(row))
        self.assertEqual(rec.registracija_mesto, "100")
        self.assertEqual(rec.registracija_broj, "200")
        self.assertEqual(rec.registracija_strana, "300")

    def test_record_has_no_registration_date_field(self):
        rec = parse_row(tuple([""] * len(SOURCE_COLUMNS)))
        self.assertFalse(hasattr(rec, "registracija_datum"))
