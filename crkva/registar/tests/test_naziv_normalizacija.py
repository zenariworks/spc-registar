"""#298: нормализација `naziv` важи и на bulk_create/bulk_update путањама.

`save()` нормализује назив, али `bulk_create`/`bulk_update` заобилазе
`save()`. `NazivQuerySet` враћа нормализацију на тим путањама, па
case-insensitive ограничење (`*_naziv_ci_uniq`) не пропушта дупликате са
вишком размака / другачијом величином слова.
"""

# pylint: disable=missing-function-docstring

from django.db import IntegrityError, transaction
from django.test import TestCase
from registar.models import Narodnost, Veroispovest, Zanimanje

MODELI = [Narodnost, Veroispovest]


class NazivBulkNormalizacijaTests(TestCase):
    def test_bulk_create_normalizuje_naziv(self):
        for model in MODELI:
            obj = model.objects.bulk_create([model(naziv="  Срб   ин  ")])[0]
            obj.refresh_from_db()
            self.assertEqual(obj.naziv, "Срб ин")

    def test_bulk_create_zanimanje_normalizuje_naziv(self):
        obj = Zanimanje.objects.bulk_create([Zanimanje(sifra="1", naziv="  Ле  кар ")])[
            0
        ]
        obj.refresh_from_db()
        self.assertEqual(obj.naziv, "Ле кар")

    def test_bulk_create_whitespace_variant_pogadja_ci_uniq(self):
        """Постојећи 'Лекар' + bulk_create 'Лекар ' → ограничење обара упис."""
        for model in MODELI:
            model.objects.create(naziv="Лекар")
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    model.objects.bulk_create([model(naziv="  Лекар  ")])
            self.assertEqual(model.objects.filter(naziv="Лекар").count(), 1)

    def test_bulk_update_normalizuje_naziv(self):
        obj = Narodnost.objects.create(naziv="Срб")
        obj.naziv = "  Срб   ин  "
        Narodnost.objects.bulk_update([obj], ["naziv"])
        obj.refresh_from_db()
        self.assertEqual(obj.naziv, "Срб ин")
