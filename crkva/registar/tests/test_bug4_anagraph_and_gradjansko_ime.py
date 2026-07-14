"""Regression: анаграф и грађанско име морају бити приказани и/или унесени."""

# pylint: disable=missing-function-docstring

import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Krstenje, Osoba
from tenants.models import Clanstvo, Uloga, Zakupac

User = get_user_model()


class KrstenjeAnagraphDisplayTests(TestCase):
    """Bug 4: анаграф поља морају бити приказана на детаљима крштења."""

    def setUp(self):
        self.client = Client()
        from django.contrib.auth import get_user_model

        _U = get_user_model()
        self.user = _U.objects.create_superuser(
            username="auto-test", email="a@a.test", password="x"
        )
        self.client.force_login(self.user)

    def test_anagraph_fields_render_on_detail(self):
        dete = Osoba.objects.create(ime="Беба", prezime="Тест", pol="М")
        k = Krstenje.objects.create(
            dete=dete,
            knjiga=1,
            strana=10,
            broj=42,
            redni_broj=1,
            godina_registracije=2024,
            vanbracno=False,
            blizanac=False,
            telesna_mana=False,
            datum=datetime.date(2024, 6, 1),
            mesto_registracije="Београд",
            datum_registracije=datetime.date(2024, 6, 2),
            maticni_broj="МБ-1234567",
            strana_registracije="A-7",
        )
        r = self.client.get(reverse("krstenje_detail", kwargs={"uid": k.uid}))
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertIn("Матични број", body)
        self.assertIn("Београд", body)
        self.assertIn("МБ-1234567", body)
        self.assertIn("A-7", body)

    def test_anagraph_section_hidden_when_all_blank(self):
        dete = Osoba.objects.create(ime="Беба2", prezime="Тест", pol="М")
        k = Krstenje.objects.create(
            dete=dete,
            knjiga=2,
            strana=11,
            broj=43,
            redni_broj=2,
            godina_registracije=2024,
            vanbracno=False,
            blizanac=False,
            telesna_mana=False,
            datum=datetime.date(2024, 7, 1),
        )
        r = self.client.get(reverse("krstenje_detail", kwargs={"uid": k.uid}))
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertNotIn("Матични број", body)


class ParohijanGradjanskoImeTests(TestCase):
    """Bug 4 (part 2): grаđansko_ime мора се чувати и приказивати."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Zakupac.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        Clanstvo.objects.create(
            korisnik=cls.clerk, parohija=cls.tenant, uloga=Uloga.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)

    def test_form_saves_gradjansko_ime(self):
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Жарко",
                "prezime": "Тест",
                "pol": "М",
                "gradjansko_ime": "Жорж",
            },
        )
        self.assertEqual(r.status_code, 302)
        osoba = Osoba.objects.get(ime="Жарко")
        self.assertEqual(osoba.gradjansko_ime, "Жорж")

    def test_detail_renders_gradjansko_ime(self):
        osoba = Osoba.objects.create(
            ime="Митар", prezime="Тест", pol="М", gradjansko_ime="Мата", parohijan=True
        )
        r = self.client.get(reverse("parohijan_detail", kwargs={"uid": osoba.uid}))
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertIn("Грађанско име", body)
        self.assertIn("Мата", body)
