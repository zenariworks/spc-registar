"""Regression test: /slava/<id>/ rendered after dropping adresa.ulica FK."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import TestCase
from registar.models import Domacinstvo, Osoba, Slava
from tenants.models import Clanstvo, Uloga, Zakupac

User = get_user_model()


class SlavaDomacinstvaViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Zakupac.objects.get(schema_name="test_tenant")
        cls.user = User.objects.create_user(username="view", password="x")
        Clanstvo.objects.create(
            korisnik=cls.user, parohija=cls.tenant, uloga=Uloga.PREGLED
        )
        cls.slava = Slava.objects.create(naziv="Тест Слава", dan=1, mesec=1)
        osoba = Osoba.objects.create(ime="Тест", prezime="Домаћин", pol="М")
        Domacinstvo.objects.create(domacin=osoba, slava=cls.slava)

    def test_slava_detail_renders(self):
        self.client.force_login(self.user)
        r = self.client.get(f"/slava/{self.slava.uid}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Тест Слава")
        self.assertEqual(r.context["count"], 1)
