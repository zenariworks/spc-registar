"""
Интеграциони тестови за веб апликацију registar.
Ови тестови проверавају интеракције између више компоненти система.
"""

import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from registar.models import Hram, Krstenje, Osoba, Svestenik, Vencanje


class KrstenjeCreationIntegrationTest(TransactionTestCase):
    """Интеграциони тестови за креирање крштења."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="testadmin", email="admin@example.com", password="testpass123"
        )
        self.hram = Hram.objects.create(naziv="Храм Светог Саве")
        self.svestenik = Svestenik.objects.create(
            ime="Петар", prezime="Петровић", zvanje="Протојереј"
        )

    def test_complete_krstenje_creation_workflow(self):
        """Тест комплетног воркфлоуа креирања крштења"""
        # Пријава као администратор
        self.client.login(username="testadmin", password="testpass123")

        # Креирање особе детета
        dete_data = {
            "ime": "Марко",
            "prezime": "Марковић",
            "datum_rodjenja": "2024-01-15",
            "pol": "М",
            "parohijan": True,
        }
        response = self.client.post(reverse("unos_parohijana"), dete_data)
        self.assertEqual(response.status_code, 302)  # Редирект након креирања

        # Добијање креиране особе
        dete = Osoba.objects.get(ime="Марко", prezime="Марковић")

        # Креирање родитеља
        otac = Osoba.objects.create(
            ime="Стефан",
            prezime="Стефановић",
            zanimanje="инжењер",
            veroispovest="православна",
            narodnost="српска",
        )
        majka = Osoba.objects.create(
            ime="Јелена",
            prezime="Стефановић",
            devojacko_prezime="Јовановић",
            zanimanje="учитељ",
            veroispovest="православна",
            narodnost="српска",
        )
        kum = Osoba.objects.create(
            ime="Милош", prezime="Милошевић", zanimanje="адвокат"
        )

        # Креирање крштења са свим потребним подацима
        krstenje_data = {
            "dete": dete.uid,
            "otac": otac.uid,
            "majka": majka.uid,
            "kum": kum.uid,
            "knjiga": 1,
            "broj": 1,
            "strana": 1,
            "redni_broj": 1,
            "godina_registracije": 2024,
            "datum": "2024-02-10",
            "vreme": "10:00",
            "mesto": "Београд",
            "adresa_deteta_grad": "Београд",
            "adresa_deteta_ulica": "ул. Николе Пашића",
            "adresa_deteta_broj": "10",
            "dete_vanbracno": False,
            "dete_blizanac": False,
            "dete_sa_telesnom_manom": False,
            "hram": self.hram.uid,
            "svestenik": self.svestenik.uid,
        }

        response = self.client.post(reverse("unos_krstenja"), krstenje_data)
        self.assertEqual(response.status_code, 302)  # Редирект након креирања

        # Верификација да је крштење креирано
        krstenje = Krstenje.objects.get(redni_broj=1)
        self.assertEqual(krstenje.dete, dete)
        self.assertEqual(krstenje.otac, otac)
        self.assertEqual(krstenje.majka, majka)
        self.assertEqual(krstenje.kum, kum)
        self.assertEqual(krstenje.hram, self.hram)
        self.assertEqual(krstenje.svestenik, self.svestenik)
        self.assertEqual(krstenje.datum, datetime.date(2024, 2, 10))
        self.assertEqual(krstenje.adresa_deteta_grad, "Београд")

    def test_krstenje_creation_page_accessible(self):
        """Тест да је страница за креирање крштења доступна"""
        response = self.client.get(reverse("unos_krstenja"))
        # Страница је доступна без пријаве (тренутна имплементација)
        self.assertEqual(response.status_code, 200)

    def test_krstenje_creation_with_invalid_data(self):
        """Тест креирања крштења са неважећим подацима"""
        self.client.login(username="testadmin", password="testpass123")

        # Покушај креирања крштења са неважећим подацима
        krstenje_data = {
            "knjiga": 0,  # Неважећа вредност - мора бити >= 1
            "broj": 1,
            "strana": 1,
            "redni_broj": 1,
            "godina_registracije": 2024,
            "datum": "2024-02-10",
            "adresa_deteta_grad": "Београд",
            "dete_vanbracno": False,
            "dete_blizanac": False,
            "dete_sa_telesnom_manom": False,
        }

        response = self.client.post(reverse("unos_krstenja"), krstenje_data)
        # Требало би да остане на истој страници због грешке
        self.assertEqual(response.status_code, 200)
        # Ниједно крштење не би требало да буде креирано због валидације
        self.assertEqual(Krstenje.objects.count(), 0)


class VencanjeCreationIntegrationTest(TransactionTestCase):
    """Интеграциони тестови за креирање венчања."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="testadmin", email="admin@example.com", password="testpass123"
        )
        self.hram = Hram.objects.create(naziv="Храм Светог Саве")
        self.svestenik = Svestenik.objects.create(
            ime="Петар", prezime="Петровић", zvanje="Протојереј"
        )

    def test_complete_vencanje_creation_workflow(self):
        """Тест комплетног воркфлоуа креирања венчања"""
        # Пријава као администратор
        self.client.login(username="testadmin", password="testpass123")

        # Креирање женика
        zenik_data = {
            "ime": "Марко",
            "prezime": "Марковић",
            "datum_rodjenja": "1990-05-15",
            "mesto_rodjenja": "Београд",
            "zanimanje": "инжењер",
            "veroispovest": "православна",
            "narodnost": "српска",
            "parohijan": True,
        }
        response = self.client.post(reverse("unos_parohijana"), zenik_data)
        self.assertEqual(response.status_code, 302)

        # Креирање невесте
        nevesta_data = {
            "ime": "Ана",
            "prezime": "Јовановић",
            "devojacko_prezime": "Јовановић",
            "datum_rodjenja": "1992-08-20",
            "mesto_rodjenja": "Нови Сад",
            "zanimanje": "учитељ",
            "veroispovest": "православна",
            "narodnost": "српска",
            "parohijan": True,
        }
        response = self.client.post(reverse("unos_parohijana"), nevesta_data)
        self.assertEqual(response.status_code, 302)

        # Добијање креираних особа
        zenik = Osoba.objects.get(ime="Марко", prezime="Марковић")
        nevesta = Osoba.objects.get(ime="Ана", prezime="Јовановић")

        # Креирање кума
        kum = Osoba.objects.create(
            ime="Стефан", prezime="Петровић", zanimanje="адвокат"
        )

        # Креирање венчања са свим потребним подацима
        vencanje_data = {
            "zenik": zenik.uid,
            "nevesta": nevesta.uid,
            "kum": kum.uid,
            "godina_registracije": 2024,
            "redni_broj": 1,
            "knjiga": 1,
            "strana": 1,
            "broj": 1,
            "datum": "2024-06-15",
            "mesto_zenika": "Београд",
            "adresa_zenika": "ул. Николе Пашића 10",
            "mesto_neveste": "Нови Сад",
            "adresa_neveste": "ул. Змаја од ноћаја 15",
            "zenik_rb_brak": 1,
            "nevesta_rb_brak": 1,
            "hram": self.hram.uid,
            "svestenik": self.svestenik.uid,
            "razresenje": True,
        }

        response = self.client.post(reverse("unos_vencanja"), vencanje_data)
        self.assertEqual(response.status_code, 302)  # Редирект након креирања

        # Верификација да је венчање креирано
        vencanje = Vencanje.objects.get(redni_broj=1)
        self.assertEqual(vencanje.zenik, zenik)
        self.assertEqual(vencanje.nevesta, nevesta)
        self.assertEqual(vencanje.kum, kum)
        self.assertEqual(vencanje.hram, self.hram)
        self.assertEqual(vencanje.svestenik, self.svestenik)
        self.assertEqual(vencanje.datum, datetime.date(2024, 6, 15))
        self.assertEqual(vencanje.mesto_zenika, "Београд")

    def test_vencanje_creation_page_accessible(self):
        """Тест да је страница за креирање венчања доступна"""
        response = self.client.get(reverse("unos_vencanja"))
        # Страница је доступна без пријаве (тренутна имплементација)
        self.assertEqual(response.status_code, 200)


class SearchIntegrationTest(TestCase):
    """Интеграциони тестови за претрагу."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Креирање табеле veroispovesti ако не постоји (unmanaged model)
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS veroispovesti (
                    uid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    naziv VARCHAR(255)
                )
            """)

    def setUp(self):
        self.client = Client()
        # Креирање тест података
        self.osoba1 = Osoba.objects.create(
            ime="Никола", prezime="Петровић", parohijan=True
        )
        self.osoba2 = Osoba.objects.create(
            ime="Ана", prezime="Јовановић", parohijan=True
        )
        self.krstenje = Krstenje.objects.create(
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )

    def test_search_functionality(self):
        """Тест функционалности претраге"""
        response = self.client.get(reverse("search_view"), {"query": "Никола"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("parohijan_results", response.context)
        results = list(response.context["parohijan_results"])
        self.assertIn(self.osoba1, results)

    def test_search_with_no_results(self):
        """Тест претраге без резултата"""
        response = self.client.get(reverse("search_view"), {"query": "Непостојећеиме"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("parohijan_results", response.context)
        results = list(response.context["parohijan_results"])
        self.assertEqual(len(results), 0)

    def test_search_with_empty_query(self):
        """Тест претраге са празним упитом"""
        response = self.client.get(reverse("search_view"), {"query": ""})
        self.assertEqual(response.status_code, 200)
        # Очекујемо празне резултате
        self.assertIn("parohijan_results", response.context)
        self.assertIn("veroisposvest_results", response.context)


class ModelRelationshipsIntegrationTest(TestCase):
    """Интеграциони тестови за релације између модела."""

    def setUp(self):
        self.hram = Hram.objects.create(naziv="Храм Светог Саве")
        self.svestenik = Svestenik.objects.create(
            ime="Петар", prezime="Петровић", zvanje="Протојереј"
        )
        self.dete = Osoba.objects.create(
            ime="Марко",
            prezime="Марковић",
            datum_rodjenja=datetime.date(2024, 1, 15),
            pol="М",
        )
        self.otac = Osoba.objects.create(
            ime="Стефан", prezime="Марковић", zanimanje="инжењер"
        )
        self.majka = Osoba.objects.create(
            ime="Ана",
            prezime="Марковић",
            devojacko_prezime="Јовановић",
            zanimanje="учитељ",
        )

    def test_krstenje_model_relationships(self):
        """Тест релација модела крштења са другим моделима"""
        krstenje = Krstenje.objects.create(
            dete=self.dete,
            otac=self.otac,
            majka=self.majka,
            hram=self.hram,
            svestenik=self.svestenik,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )

        # Провера свих релација
        self.assertEqual(krstenje.dete, self.dete)
        self.assertEqual(krstenje.otac, self.otac)
        self.assertEqual(krstenje.majka, self.majka)
        self.assertEqual(krstenje.hram, self.hram)
        self.assertEqual(krstenje.svestenik, self.svestenik)

        # Провера пропертија
        self.assertEqual(krstenje.ime_deteta, "Марко")
        self.assertEqual(krstenje.ime_oca, "Стефан")
        self.assertEqual(krstenje.ime_majke, "Ана")

    def test_cascade_deletion_relationships(self):
        """Тест ON DELETE понашања релација"""
        krstenje = Krstenje.objects.create(
            dete=self.dete,
            otac=self.otac,
            majka=self.majka,
            hram=self.hram,
            svestenik=self.svestenik,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )

        # Брисање особе детета
        self.dete.delete()

        # Освежавање објекта из базе
        krstenje.refresh_from_db()

        # Провера да је референца постављена на NULL
        self.assertIsNone(krstenje.dete)

        # Остали подаци остају нетакнути
        self.assertEqual(krstenje.otac, self.otac)
        self.assertEqual(krstenje.majka, self.majka)
        self.assertEqual(krstenje.hram, self.hram)
        self.assertEqual(krstenje.svestenik, self.svestenik)


class FormValidationIntegrationTest(TestCase):
    """Интеграциони тестови за валидацију форми."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="testadmin", email="admin@example.com", password="testpass123"
        )

    def test_krstenje_form_validation_negative_values(self):
        """Тест валидације форме крштења са негативним вредностима"""
        self.client.login(username="testadmin", password="testpass123")

        # Покушај са негативним вредностима које би требало да буду позитивне
        krstenje_data = {
            "knjiga": -1,  # Негативна вредност
            "broj": 1,
            "strana": 1,
            "redni_broj": 1,
            "godina_registracije": 2024,
            "datum": "2024-02-10",
            "adresa_deteta_grad": "Београд",
            "dete_vanbracno": False,
            "dete_blizanac": False,
            "dete_sa_telesnom_manom": False,
        }

        response = self.client.post(reverse("unos_krstenja"), krstenje_data)
        # Форма треба да буде поново приказана са грешкама
        self.assertEqual(response.status_code, 200)
        # Ниједно крштење не би требало да буде креирано због валидације
        self.assertEqual(Krstenje.objects.count(), 0)

    def test_vencanje_form_validation_past_year(self):
        """Тест валидације форме венчања са прошлом годином"""
        self.client.login(username="testadmin", password="testpass123")

        past_year = 1800  # Неважећа година
        vencanje_data = {
            "godina_registracije": past_year,
            "redni_broj": 1,
            "knjiga": 1,
            "strana": 1,
            "broj": 1,
            "datum": f"{past_year}-06-15",
        }

        response = self.client.post(reverse("unos_vencanja"), vencanje_data)
        # Форма треба да буде поново приказана са грешкама
        self.assertEqual(response.status_code, 200)
        # Ниједно венчање не би требало да буде креирано због валидације
        self.assertEqual(Vencanje.objects.count(), 0)


class CrossModelReferenceTest(TestCase):
    """Тестови за унакрсне референце између модела."""

    def setUp(self):
        self.zenik = Osoba.objects.create(
            ime="Марко", prezime="Марковић", parohijan=True
        )
        self.nevesta = Osoba.objects.create(
            ime="Ана", prezime="Јовановић", parohijan=True
        )
        self.dete = Osoba.objects.create(
            ime="Петар", prezime="Марковић", parohijan=True
        )

    def test_osoba_used_in_multiple_contexts(self):
        """Тест да се иста особа може користити у више контекста"""
        # Особа је женик у венчању
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

        # Иста особа је дете у крштењу
        krstenje = Krstenje.objects.create(
            dete=self.zenik,  # Исто лице као женик
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )

        # Провера да су оба креирана
        self.assertIsNotNone(vencanje)
        self.assertIsNotNone(krstenje)

        # Провера да је особа повезана са оба
        self.assertEqual(vencanje.zenik, self.zenik)
        self.assertEqual(krstenje.dete, self.zenik)
