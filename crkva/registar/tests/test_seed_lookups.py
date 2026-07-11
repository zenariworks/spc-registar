"""#340: seed_lookups сеје равне шифарнике data-driven из CSV.

Спојене команде unos_narodnosti/veroispovesti/zanimanja/eparhija у једну
data-driven петљу; unos_slava (покретни празници) остаје засебно.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access

from django.test import TestCase
from registar.management.commands.seed_lookups import SIFARNICI, Command
from registar.models import Eparhija, Narodnost


def _sifarnik(model):
    return next(s for s in SIFARNICI if s.model is model)


class SeedLookupsTests(TestCase):
    def test_flat_sifarnik_seeds_and_is_idempotent(self):
        cmd = Command()
        sif = _sifarnik(Narodnost)
        prvo = cmd._zasej(sif)
        self.assertGreater(prvo, 0)
        self.assertEqual(Narodnost.objects.count(), prvo)

        drugo = cmd._zasej(sif)
        self.assertEqual(drugo, 0)
        self.assertEqual(Narodnost.objects.count(), prvo)

    def test_eparhija_defaults_applied(self):
        cmd = Command()
        cmd._zasej(_sifarnik(Eparhija))
        bachka = Eparhija.objects.get(naziv="бачка")
        self.assertEqual(bachka.nivo, "Епархија")
        self.assertEqual(bachka.sediste, "Нови Сад")
