"""
Тестови за модел венчања у апликацији registar.
"""

import datetime
import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase
from registar.models import (
    Adresa,
    Hram,
    Narodnost,
    Osoba,
    Svestenik,
    Vencanje,
    Veroispovest,
    Zanimanje,
)


class VencanjeModelTestCase(TestCase):
    """Тестови за модел Vencanje."""

    def setUp(self):
        """Постављање тест података."""
        self.vera = Veroispovest.objects.create(naziv="Православна")
        self.narod = Narodnost.objects.create(naziv="Српска")

        self.z_inzenjer = Zanimanje.objects.create(naziv="инжењер", sifra="")
        self.z_ucitelj = Zanimanje.objects.create(naziv="учитељ", sifra="")
        self.zenik = Osoba.objects.create(
            ime="Марко",
            prezime="Марковић",
            datum_rodjenja=datetime.date(1990, 5, 15),
            mesto_rodjenja="Београд",
            zanimanje=self.z_inzenjer,
            veroispovest=self.vera,
            narodnost=self.narod,
        )
        self.nevesta = Osoba.objects.create(
            ime="Ана",
            prezime="Јовановић",
            devojacko_prezime="Јовановић",
            datum_rodjenja=datetime.date(1992, 8, 20),
            mesto_rodjenja="Нови Сад",
            zanimanje=self.z_ucitelj,
            veroispovest=self.vera,
            narodnost=self.narod,
        )
        self.kum = Osoba.objects.create(
            ime="Стефан",
            prezime="Петровић",
            zanimanje=None,
        )
        self.hram = Hram.objects.create(naziv="Храм Светог Саве")
        self.svestenik = Svestenik.objects.create(
            ime="Петар", prezime="Петровић", zvanje="Протојереј"
        )

    def test_create_vencanje_basic(self):
        """Креирање венчања са основним подацима."""
        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )
        self.assertIsInstance(vencanje.uid, uuid.UUID)
        self.assertEqual(vencanje.zenik, self.zenik)
        self.assertEqual(vencanje.nevesta, self.nevesta)
        self.assertEqual(vencanje.godina_registracije, 2024)
        self.assertEqual(vencanje.redni_broj, 1)

    def test_vencanje_str_representation(self):
        """Стринг репрезентација венчања."""
        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )
        self.assertIn("Венчање", str(vencanje))
        self.assertIn("Марко", str(vencanje))
        self.assertIn("Ана", str(vencanje))

    def test_vencanje_properties_zenik(self):
        """Тест пропертија за податке о женику."""
        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )

        self.assertEqual(vencanje.ime_zenika, "Марко")
        self.assertEqual(vencanje.prezime_zenika, "Марковић")
        self.assertEqual(vencanje.zanimanje_zenika, "инжењер")
        self.assertEqual(str(vencanje.veroispovest_zenika), "Православна")
        self.assertEqual(str(vencanje.narodnost_zenika), "Српска")
        self.assertEqual(vencanje.datum_rodjenja_zenika, datetime.date(1990, 5, 15))
        self.assertEqual(vencanje.mesto_rodjenja_zenika, "Београд")

    def test_vencanje_properties_nevesta(self):
        """Тест пропертија за податке о невести."""
        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )

        self.assertEqual(vencanje.ime_neveste, "Ана")
        self.assertEqual(vencanje.prezime_neveste, "Јовановић")
        self.assertEqual(vencanje.zanimanje_neveste, "учитељ")
        self.assertEqual(str(vencanje.veroispovest_neveste), "Православна")
        self.assertEqual(str(vencanje.narodnost_neveste), "Српска")
        self.assertEqual(vencanje.datum_rodjenja_neveste, datetime.date(1992, 8, 20))
        self.assertEqual(vencanje.mesto_rodjenja_neveste, "Нови Сад")

    def test_vencanje_properties_without_linked_persons(self):
        """Тест пропертија када особе нису повезане."""
        vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )

        self.assertEqual(vencanje.ime_zenika, "")
        self.assertEqual(vencanje.prezime_zenika, "")
        self.assertEqual(vencanje.zanimanje_zenika, "")
        self.assertEqual(vencanje.veroispovest_zenika, "")
        self.assertEqual(vencanje.narodnost_zenika, "")
        self.assertIsNone(vencanje.datum_rodjenja_zenika)
        self.assertEqual(vencanje.mesto_rodjenja_zenika, "")

        self.assertEqual(vencanje.ime_neveste, "")
        self.assertEqual(vencanje.prezime_neveste, "")
        self.assertEqual(vencanje.zanimanje_neveste, "")
        self.assertEqual(vencanje.veroispovest_neveste, "")
        self.assertEqual(vencanje.narodnost_neveste, "")
        self.assertIsNone(vencanje.datum_rodjenja_neveste)
        self.assertEqual(vencanje.mesto_rodjenja_neveste, "")

    def test_vencanje_with_all_relations(self):
        """Креирање венчања са свим повезаним особама."""
        svekar = Osoba.objects.create(ime="Петар", prezime="Марковић")
        svekrva = Osoba.objects.create(ime="Јелена", prezime="Марковић")
        tast = Osoba.objects.create(ime="Борис", prezime="Јовановић")
        tasta = Osoba.objects.create(ime="Милена", prezime="Јовановић")
        stari_svat = Osoba.objects.create(ime="Милош", prezime="Петровић")

        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            kum=self.kum,
            svekar=svekar,
            svekrva=svekrva,
            tast=tast,
            tasta=tasta,
            stari_svat=stari_svat,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
            hram=self.hram,
            svestenik=self.svestenik,
        )

        self.assertEqual(vencanje.kum, self.kum)
        self.assertEqual(vencanje.svekar, svekar)
        self.assertEqual(vencanje.svekrva, svekrva)
        self.assertEqual(vencanje.tast, tast)
        self.assertEqual(vencanje.tasta, tasta)
        self.assertEqual(vencanje.stari_svat, stari_svat)
        self.assertEqual(vencanje.hram, self.hram)
        self.assertEqual(vencanje.svestenik, self.svestenik)

    def test_vencanje_validators_godina_registracije(self):
        """Валидација минималне вредности за годину регистрације."""
        vencanje = Vencanje(
            godina_registracije=1800,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )
        with self.assertRaises(ValidationError):
            vencanje.full_clean()

    def test_vencanje_validators_redni_broj(self):
        """Валидација минималне вредности за редни број."""
        vencanje = Vencanje(
            godina_registracije=2024,
            redni_broj=0,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )
        with self.assertRaises(ValidationError):
            vencanje.full_clean()

    def test_vencanje_validators_knjiga(self):
        """Валидација минималне вредности за књигу."""
        vencanje = Vencanje(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=0,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )
        with self.assertRaises(ValidationError):
            vencanje.full_clean()

    def test_vencanje_validators_strana(self):
        """Валидација минималне вредности за страну."""
        vencanje = Vencanje(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=0,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )
        with self.assertRaises(ValidationError):
            vencanje.full_clean()

    def test_vencanje_validators_broj(self):
        """Валидација минималне вредности за текући број."""
        vencanje = Vencanje(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=0,
            datum=datetime.date(2024, 6, 15),
        )
        with self.assertRaises(ValidationError):
            vencanje.full_clean()

    def test_on_delete_set_null(self):
        """Брисање особе поставља NULL на венчању."""
        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )

        vencanje_uid = vencanje.uid
        self.zenik.delete()
        vencanje.refresh_from_db()
        self.assertIsNone(vencanje.zenik)
        self.assertEqual(vencanje.uid, vencanje_uid)

    def test_vencanje_with_additional_fields(self):
        """Креирање венчања са додатним пољима."""
        adresa_z = Adresa.objects.create(
            mesto="Београд", ulica="ул. Николе Пашића", broj="10"
        )
        adresa_n = Adresa.objects.create(
            mesto="Нови Сад", ulica="ул. Змаја од ноћаја", broj="15"
        )
        self.zenik.adresa = adresa_z
        self.zenik.save()
        self.nevesta.adresa = adresa_n
        self.nevesta.save()

        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
            zenik_rb_brak=1,
            nevesta_rb_brak=1,
            datum_ispita=datetime.date(2024, 6, 1),
            hram=self.hram,
            svestenik=self.svestenik,
            razresenje=True,
            primedba="Напомена за венчање",
        )

        self.assertEqual(vencanje.adresa_zenika.mesto, "Београд")
        self.assertEqual(vencanje.adresa_neveste.mesto, "Нови Сад")
        self.assertEqual(vencanje.zenik_rb_brak, 1)
        self.assertEqual(vencanje.nevesta_rb_brak, 1)
        self.assertEqual(vencanje.datum_ispita, datetime.date(2024, 6, 1))
        self.assertEqual(vencanje.hram, self.hram)
        self.assertEqual(vencanje.svestenik, self.svestenik)
        self.assertTrue(vencanje.razresenje)
        self.assertEqual(vencanje.primedba, "Напомена за венчање")

    def test_vencanje_default_values(self):
        """Тест подразумеваних вредности."""
        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            datum=datetime.date(2024, 6, 15),
        )

        self.assertEqual(vencanje.godina_registracije, 2000)
        self.assertEqual(vencanje.redni_broj, 1)
        self.assertEqual(vencanje.knjiga, 1)
        self.assertEqual(vencanje.strana, 1)
        self.assertEqual(vencanje.broj, 1)
        self.assertTrue(vencanje.razresenje)
        self.assertEqual(vencanje.primedba, "")


class VencanjeModelEdgeCasesTestCase(TestCase):
    """Тестови за граничне случајеве модела венчања."""

    def test_vencanje_with_adresa_on_osoba(self):
        """Тест венчања са адресом на Osoba."""
        adresa = Adresa.objects.create(mesto="Тест", ulica="Тест улица", broj="1")
        zenik = Osoba.objects.create(ime="Тест", prezime="Тестић", adresa=adresa)
        vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
            zenik=zenik,
        )
        self.assertEqual(vencanje.adresa_zenika.mesto, "Тест")

    def test_vencanje_with_future_date(self):
        """Тест венчања са датумом у будућности."""
        future_date = datetime.date.today() + datetime.timedelta(days=365)
        vencanje = Vencanje.objects.create(
            godina_registracije=future_date.year,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=future_date,
        )
        self.assertEqual(vencanje.datum, future_date)

    def test_vencanje_without_required_date(self):
        """Тест венчања без датума (nullable field)."""
        vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
        )
        self.assertIsNone(vencanje.datum)

    def test_vencanje_with_zero_values_for_optional_numeric_fields(self):
        """Тест венчања са нултим вредностима за опционе нумеричке поља."""
        vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
            zenik_rb_brak=0,
            nevesta_rb_brak=0,
        )
        self.assertEqual(vencanje.zenik_rb_brak, 0)
        self.assertEqual(vencanje.nevesta_rb_brak, 0)
