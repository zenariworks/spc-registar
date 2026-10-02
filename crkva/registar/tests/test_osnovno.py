"""Пакетни упис у MigrationCommand (registar.uvoz.osnovno)."""

from io import StringIO

from django.test import TestCase
from registar.models import Domacinstvo, Osoba, Ukucanin
from registar.uvoz.osnovno import MigrationCommand


class UkucaniUvoz(MigrationCommand):
    """Најмања миграција са циљним моделом Ukucanin (аутоматски PK)."""

    target_model = Ukucanin


class MigrateInBatchesTests(TestCase):
    """Број нових уноса мора да прати стварни упис у базу."""

    @classmethod
    def setUpTestData(cls):
        cls.domacin = Osoba.objects.create(ime="Петар", prezime="Петровић")
        cls.dom = Domacinstvo.objects.create(domacin=cls.domacin)
        cls.clanovi = [
            Osoba.objects.create(ime=ime, prezime="Петровић")
            for ime in ("Ана", "Марко", "Јана")
        ]
        Ukucanin.objects.create(domacinstvo=cls.dom, osoba=cls.clanovi[0])

    def _uvezi(self, zapisi, **kwargs):
        komanda = UkucaniUvoz(stdout=StringIO())
        return komanda.migrate_in_batches(iter(zapisi), **kwargs)

    def _zapisi(self):
        """Три члана (први већ постоји у домаћинству) и један празан запис."""
        return [{"domacinstvo": self.dom, "osoba": o} for o in self.clanovi] + [None]

    def test_counts_inserted_rows(self):
        """Броје се само стварно уписани редови, без конфликтног."""
        created = self._uvezi(self._zapisi())
        self.assertEqual(created, 2)
        self.assertEqual(Ukucanin.objects.filter(domacinstvo=self.dom).count(), 3)

    def test_counts_across_batches(self):
        """Збир важи и кад се упис дели у више пакета."""
        self.assertEqual(self._uvezi(self._zapisi(), batch_size=2), 2)

    def test_rows_without_person_are_all_inserted(self):
        """Редови без особе нису под ограничењем и сви се броје."""
        zapisi = [
            {"domacinstvo": self.dom, "ime_ukucana": f"Члан {i}"} for i in range(3)
        ]
        self.assertEqual(self._uvezi(zapisi), 3)

    def test_dry_run_estimates_without_writing(self):
        """--dry-run процењује број редова и ништа не уписује."""
        created = self._uvezi(self._zapisi(), dry_run=True)
        self.assertEqual(created, 3)
        self.assertEqual(Ukucanin.objects.filter(domacinstvo=self.dom).count(), 1)
