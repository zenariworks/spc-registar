"""
Тестови за моделе у апликацији registar.
"""

import datetime
import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase
from registar.models import Hram, Krstenje, Osoba


class KrstenjeModelTestCase(TestCase):
    """Тестови за модел Krstenje."""

    def setUp(self):
        """Постављање тест података."""
        self.dete = Osoba.objects.create(
            ime="Петар",
            prezime="Петровић",
            datum_rodjenja=datetime.date(2024, 1, 15),
            vreme_rodjenja=datetime.time(10, 30),
            mesto_rodjenja="Београд",
            pol="М",
        )
        self.otac = Osoba.objects.create(
            ime="Марко",
            prezime="Петровић",
            zanimanje="инжењер",
            veroispovest="православна",
            narodnost="српска",
        )
        self.majka = Osoba.objects.create(
            ime="Ана",
            prezime="Петровић",
            devojacko_prezime="Јовановић",
            zanimanje="лекар",
        )
        self.kum = Osoba.objects.create(
            ime="Стефан",
            prezime="Стефановић",
            zanimanje="адвокат",
        )
        self.hram = Hram.objects.create(naziv="Храм Светог Саве")

    def test_create_krstenje(self):
        """Креирање крштења са основним подацима."""
        krstenje = Krstenje.objects.create(
            dete=self.dete,
            otac=self.otac,
            majka=self.majka,
            kum=self.kum,
            hram=self.hram,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            vreme=datetime.time(11, 0),
            mesto="Београд",
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.assertIsInstance(krstenje.uid, uuid.UUID)
        self.assertEqual(krstenje.knjiga, 1)

    def test_krstenje_str(self):
        """Стринг репрезентација крштења је UID."""
        krstenje = Krstenje.objects.create(
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.assertEqual(str(krstenje), str(krstenje.uid))

    def test_property_ime_deteta(self):
        """Проперти за име детета."""
        krstenje = Krstenje.objects.create(
            dete=self.dete,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.assertEqual(krstenje.ime_deteta, "Петар")

    def test_property_ime_deteta_none(self):
        """Проперти за име детета када дете није повезано."""
        krstenje = Krstenje.objects.create(
            dete=None,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.assertEqual(krstenje.ime_deteta, "")

    def test_property_datum_rodjenja(self):
        """Проперти за датум рођења детета."""
        krstenje = Krstenje.objects.create(
            dete=self.dete,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.assertEqual(krstenje.datum_rodjenja, datetime.date(2024, 1, 15))

    def test_property_ime_oca(self):
        """Проперти за име оца."""
        krstenje = Krstenje.objects.create(
            otac=self.otac,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.assertEqual(krstenje.ime_oca, "Марко")
        self.assertEqual(krstenje.prezime_oca, "Петровић")
        self.assertEqual(krstenje.zanimanje_oca, "инжењер")

    def test_property_ime_majke(self):
        """Проперти за име мајке."""
        krstenje = Krstenje.objects.create(
            majka=self.majka,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.assertEqual(krstenje.ime_majke, "Ана")
        self.assertEqual(krstenje.prezime_majke, "Петровић")

    def test_property_ime_kuma(self):
        """Проперти за име кума."""
        krstenje = Krstenje.objects.create(
            kum=self.kum,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.assertEqual(krstenje.ime_kuma, "Стефан")
        self.assertEqual(krstenje.zanimanje_kuma, "адвокат")

    def test_knjiga_min_validator(self):
        """Валидација минималне вредности за књигу."""
        krstenje = Krstenje(
            knjiga=0,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        with self.assertRaises(ValidationError):
            krstenje.full_clean()

    def test_on_delete_set_null(self):
        """Брисање особе поставља NULL на крштењу."""
        krstenje = Krstenje.objects.create(
            dete=self.dete,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.dete.delete()
        krstenje.refresh_from_db()
        self.assertIsNone(krstenje.dete)


class HramModelTestCase(TestCase):
    """Тестови за модел Hram."""

    def test_create_hram(self):
        """Креирање храма."""
        hram = Hram.objects.create(naziv="Храм Светог Саве")
        self.assertEqual(hram.naziv, "Храм Светог Саве")

    def test_str_representation(self):
        """Стринг репрезентација храма."""
        hram = Hram.objects.create(naziv="Саборна црква")
        self.assertEqual(str(hram), "Саборна црква")
