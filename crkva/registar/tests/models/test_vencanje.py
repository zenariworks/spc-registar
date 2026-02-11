"""
Тестови за модел венчања у апликацији registar.
"""

import datetime
import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase
from registar.models import Hram, Osoba, Svestenik, Vencanje


class VencanjeModelTestCase(TestCase):
    """Тестови за модел Vencanje."""

    def setUp(self):
        """Постављање тест података."""
        self.zenik = Osoba.objects.create(
            ime="Марко",
            prezime="Марковић",
            datum_rodjenja=datetime.date(1990, 5, 15),
            mesto_rodjenja="Београд",
            zanimanje="инжењер",
            veroispovest="православна",
            narodnost="српска",
        )
        self.nevesta = Osoba.objects.create(
            ime="Ана",
            prezime="Јовановић",
            devojacko_prezime="Јовановић",
            datum_rodjenja=datetime.date(1992, 8, 20),
            mesto_rodjenja="Нови Сад",
            zanimanje="учитељ",
            veroispovest="православна",
            narodnost="српска",
        )
        self.kum = Osoba.objects.create(
            ime="Стефан",
            prezime="Петровић",
            zanimanje="адвокат",
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
        """Стринг репрезентација венчања је UID."""
        vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
        )
        self.assertEqual(str(vencanje), str(vencanje.uid))

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
        self.assertEqual(vencanje.veroispovest_zenika, "православна")
        self.assertEqual(vencanje.narodnost_zenika, "српска")
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
        self.assertEqual(vencanje.prezime_neveste, "Јовановић")  # девојачко презиме
        self.assertEqual(vencanje.zanimanje_neveste, "учитељ")
        self.assertEqual(vencanje.veroispovest_neveste, "православна")
        self.assertEqual(vencanje.narodnost_neveste, "српска")
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
            godina_registracije=1800,  # Неважећа година
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
            redni_broj=0,  # Неважећи редни број
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
            knjiga=0,  # Неважећа књига
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
            strana=0,  # Неважећа страна
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
            broj=0,  # Неважећи текући број
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

        # Сачувај UID пре брисања
        vencanje_uid = vencanje.uid

        # Обриши женика
        self.zenik.delete()

        # Освежи објекат из базе
        vencanje.refresh_from_db()
        self.assertIsNone(vencanje.zenik)
        self.assertEqual(vencanje.uid, vencanje_uid)  # UID треба да буде исти

    def test_vencanje_with_additional_fields(self):
        """Креирање венчања са додатним пољима."""
        vencanje = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
            mesto_zenika="Београд",
            adresa_zenika="ул. Николе Пашића 10",
            mesto_neveste="Нови Сад",
            adresa_neveste="ул. Змаја од ноћаја 15",
            zenik_rb_brak=1,
            nevesta_rb_brak=1,
            datum_ispita=datetime.date(2024, 6, 1),
            hram=self.hram,
            svestenik=self.svestenik,
            razresenje=True,
            primedba="Напомена за венчање",
        )

        self.assertEqual(vencanje.mesto_zenika, "Београд")
        self.assertEqual(vencanje.adresa_zenika, "ул. Николе Пашића 10")
        self.assertEqual(vencanje.mesto_neveste, "Нови Сад")
        self.assertEqual(vencanje.adresa_neveste, "ул. Змаја од ноћаја 15")
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

        # Провери подразумеване вредности
        self.assertEqual(vencanje.godina_registracije, 2000)  # подразумевана вредност
        self.assertEqual(vencanje.redni_broj, 1)  # подразумевана вредност
        self.assertEqual(vencanje.knjiga, 1)  # подразумевана вредност
        self.assertEqual(vencanje.strana, 1)  # подразумевана вредност
        self.assertEqual(vencanje.broj, 1)  # подразумевана вредност
        self.assertTrue(vencanje.razresenje)  # подразумевана вредност
        self.assertEqual(vencanje.primedba, "")  # подразумевана вредност


class VencanjeModelEdgeCasesTestCase(TestCase):
    """Тестови за граничне случајеве модела венчања."""

    def test_vencanje_with_long_text_fields(self):
        """Тест венчања са дугим текстуалним пољима."""
        long_text = "x" * 255  # Максимална дужина за CharField
        vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 15),
            mesto_zenika=long_text,
            adresa_zenika=long_text,
            mesto_neveste=long_text,
            adresa_neveste=long_text,
        )
        self.assertEqual(vencanje.mesto_zenika, long_text)

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
            # datum је nullable, тако да га не постављамо
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
            zenik_rb_brak=0,  # Ово би требало да буде 1 као минимум, али ако је nullable онда OK
            nevesta_rb_brak=0,
        )
        self.assertEqual(vencanje.zenik_rb_brak, 0)
        self.assertEqual(vencanje.nevesta_rb_brak, 0)
