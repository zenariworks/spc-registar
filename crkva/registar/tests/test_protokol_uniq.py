"""Јединственост протоколарног броја крштења и венчања (#251).

Крштења и венчања су званични протоколарни записи. У оквиру једне године
регистрације редни број мора бити јединствен — то је гаранција коју матична
књига правно пружа. Раније ниједно ограничење (ни модел, ни форма) то није
спречавало; постојао је само не-јединствени композитни индекс.

(knjiga, strana, broj) се намерно НЕ ограничава — стварни подаци садрже
легитимна понављања физичке локације уписа.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from registar.models import Krstenje, Vencanje


class KrstenjeProtokolUniqTests(TestCase):
    def test_constraint_declared(self):
        names = {c.name for c in Krstenje._meta.constraints}
        self.assertIn("krstenje_god_redni_uniq", names)

    def test_duplicate_god_redni_raises_integrity_error(self):
        Krstenje.objects.create(godina_registracije=2020, redni_broj=1, strana=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Krstenje.objects.create(
                    godina_registracije=2020, redni_broj=1, strana=2
                )

    def test_duplicate_god_redni_fails_model_validation(self):
        Krstenje.objects.create(godina_registracije=2020, redni_broj=1, strana=1)
        dup = Krstenje(godina_registracije=2020, redni_broj=1, strana=2)
        with self.assertRaises(ValidationError):
            dup.full_clean()

    def test_same_redni_different_year_allowed(self):
        Krstenje.objects.create(godina_registracije=2020, redni_broj=1, strana=1)
        Krstenje.objects.create(godina_registracije=2021, redni_broj=1, strana=1)
        self.assertEqual(Krstenje.objects.filter(redni_broj=1).count(), 2)

    def test_same_year_different_redni_allowed(self):
        Krstenje.objects.create(godina_registracije=2020, redni_broj=1, strana=1)
        Krstenje.objects.create(godina_registracije=2020, redni_broj=2, strana=1)
        self.assertEqual(
            Krstenje.objects.filter(godina_registracije=2020).count(), 2
        )

    def test_knjiga_strana_broj_repetition_allowed(self):
        # Физичка локација сме да се понови (нпр. иста страна/број, друг редни).
        Krstenje.objects.create(
            godina_registracije=2020, redni_broj=1, knjiga=1, strana=5, broj=3
        )
        Krstenje.objects.create(
            godina_registracije=2020, redni_broj=2, knjiga=1, strana=5, broj=3
        )
        self.assertEqual(Krstenje.objects.count(), 2)


class VencanjeProtokolUniqTests(TestCase):
    def test_constraint_declared(self):
        names = {c.name for c in Vencanje._meta.constraints}
        self.assertIn("vencanje_god_redni_uniq", names)

    def test_duplicate_god_redni_raises_integrity_error(self):
        Vencanje.objects.create(godina_registracije=2020, redni_broj=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vencanje.objects.create(godina_registracije=2020, redni_broj=1)

    def test_duplicate_god_redni_fails_model_validation(self):
        Vencanje.objects.create(godina_registracije=2020, redni_broj=1)
        dup = Vencanje(godina_registracije=2020, redni_broj=1)
        with self.assertRaises(ValidationError):
            dup.full_clean()

    def test_same_redni_different_year_allowed(self):
        Vencanje.objects.create(godina_registracije=2020, redni_broj=1)
        Vencanje.objects.create(godina_registracije=2021, redni_broj=1)
        self.assertEqual(Vencanje.objects.filter(redni_broj=1).count(), 2)
