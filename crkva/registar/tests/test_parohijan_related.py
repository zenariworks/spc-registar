"""Tests for parent / extended-role surfacing on parohijan detail."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from registar.models import Hram, Krstenje, Osoba, Vencanje

User = get_user_model()


class ParohijanRelatedRecordsTest(TestCase):
    """Parohijan detail must link to vencanja where the person is a parent or stari svat,
    and to krstenja where the person is otac or majka."""

    @classmethod
    def setUpTestData(cls):
        cls.hram = Hram.objects.create(naziv="Тест", mesto="Тест")
        cls.parohijan = Osoba.objects.create(
            ime="Тодора", prezime="Тузев", parohijan=True
        )
        cls.zenik = Osoba.objects.create(ime="Божидар", prezime="Ђорђевић")
        cls.nevesta = Osoba.objects.create(ime="Маја", prezime="Бојић")
        cls.vencanje = Vencanje.objects.create(
            godina_registracije=2026,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            zenik=cls.zenik,
            nevesta=cls.nevesta,
            svekrva=cls.parohijan,
            hram=cls.hram,
        )

        cls.dete = Osoba.objects.create(ime="Петар", prezime="Тузев")
        cls.parent = Osoba.objects.create(ime="Никола", prezime="Тузев", parohijan=True)
        cls.krstenje = Krstenje.objects.create(
            godina_registracije=2026,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
            dete=cls.dete,
            otac=cls.parent,
            hram=cls.hram,
        )

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)

    def test_vencanje_link_appears_for_svekrva_role(self):
        response = self.client.get(
            reverse("parohijan_detail", kwargs={"uid": self.parohijan.uid})
        )
        body = response.content.decode()
        self.assertIn("мајка женика", body)
        self.assertIn(str(self.vencanje.uid), body)

    def test_krstenje_link_appears_for_otac_role(self):
        response = self.client.get(
            reverse("parohijan_detail", kwargs={"uid": self.parent.uid})
        )
        body = response.content.decode()
        self.assertIn(str(self.krstenje.uid), body)
        self.assertIn("отац", body)
