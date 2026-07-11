"""resolve_slava: превод старе DOM_RBRSL сифре у исправан Slava ред (#255).

Покретне славе морају да се вежу за засебни покретни ред (offset_dani), а не
за фиксног свеца кога је #259 вратио на тај датум. Фиксне иду по PK == сифра.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.core.management import call_command
from django.test import TestCase
from kalendar.models import Slava
from registar.migracija.slava_map import POKRETNE_SLAVE_OFFSET_BY_SIFRA, resolve_slava
from registar.seed.unos_slava import Command as UnosSlava


class ResolveSlavaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Засеј целу славу из slave.jsonl (377: 365 фиксних + 12 покретних).
        call_command(UnosSlava())

    def test_none_uid_returns_none(self):
        self.assertIsNone(resolve_slava(None, Slava))
        self.assertIsNone(resolve_slava(0, Slava))

    def test_every_legacy_moveable_sifra_resolves_to_moveable_row(self):
        for sifra, offset in POKRETNE_SLAVE_OFFSET_BY_SIFRA.items():
            slava = resolve_slava(sifra, Slava)
            self.assertIsNotNone(slava, f"сифра {sifra} није разрешена")
            self.assertTrue(slava.pokretni, f"сифра {sifra} није покретна")
            self.assertEqual(slava.offset_dani, offset)

    def test_map_offsets_unique_and_present(self):
        # Сваки помак из мапе постоји тачно једном међу покретним редовима.
        for offset in set(POKRETNE_SLAVE_OFFSET_BY_SIFRA.values()):
            self.assertEqual(
                Slava.objects.filter(pokretni=True, offset_dani=offset).count(), 1
            )

    def test_lazareva_subota_sifra_93(self):
        # Регресија: сифра 93 је била „Лазарева субота“ (16 домаћинстава).
        slava = resolve_slava(93, Slava)
        self.assertTrue(slava.pokretni)
        self.assertIn("Лазарева", slava.naziv)

    def test_fixed_sifra_resolves_by_pk(self):
        fix = Slava.objects.create(
            naziv="Тест фиксни празник", dan=2, mesec=2, pokretni=False
        )
        self.assertNotIn(fix.uid, POKRETNE_SLAVE_OFFSET_BY_SIFRA)
        self.assertEqual(resolve_slava(fix.uid, Slava), fix)

    def test_seeded_fixed_feast_resolves_by_its_own_pk(self):
        # Фиксни празник се разрешава преко свог PK. Не тврдимо апсолутну
        # вредност uid-а: AutoField секвенца је дељена кроз цео тест-рун и
        # напредује од претходних тестова, па uid==сифра важи само на
        # свежем сеаду (rebuild), не у пуном сету. Тражимо стваран фиксни
        # ред (Никола) по називу и проверавамо разрешење по његовом PK.
        nikola = (
            Slava.objects.filter(pokretni=False, naziv__icontains="Никола")
            .exclude(uid__in=POKRETNE_SLAVE_OFFSET_BY_SIFRA)
            .first()
        )
        self.assertIsNotNone(nikola)
        self.assertEqual(resolve_slava(nikola.uid, Slava), nikola)
