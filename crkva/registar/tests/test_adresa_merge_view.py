"""Тестови за приказе спајања адреса (duplikati_adresa + spoji_adresu).

Покрива: листу кандидата-дупликата (админ), извршење спајања (POST →
пресмеравање + редирект), self-merge гард (ValueError → flash), захтев
дозволе (не-админ → 403) и require_POST (GET → 405).
Issue #222 — views/adresa_view.py био на 34%.
"""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Adresa, Osoba
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class AdresaMergeViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.admin = User.objects.create_user(username="adm", password="x")
        UserMembership.objects.create(
            user=cls.admin, tenant=cls.tenant, role=Role.ADMIN
        )
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    def _make_dup_pair(self):
        # Исти нормализовани кључ (strip+lower), али различити под Lower()
        # захваљујући размацима — пролази unique_adresa_normalized.
        a = Adresa.objects.create(ulica="Главна", broj="1", mesto="Београд")
        b = Adresa.objects.create(ulica=" Главна ", broj="1", mesto="Београд")
        return a, b

    def test_duplikati_lists_group_for_admin(self):
        self._make_dup_pair()
        r = self.client.get(reverse("duplikati_adresa"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["total_groups"], 1)
        self.assertContains(r, "Главна")

    def test_duplikati_forbidden_for_non_admin(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("duplikati_adresa"))
        self.assertEqual(r.status_code, 403)

    def test_spoji_merges_and_redirects(self):
        loser, winner = self._make_dup_pair()
        osoba = Osoba.objects.create(ime="Веза", prezime="Веза", adresa=loser)
        r = self.client.post(
            reverse(
                "spoji_adresu",
                kwargs={"loser_uid": loser.uid, "winner_uid": winner.uid},
            )
        )
        self.assertRedirects(r, reverse("duplikati_adresa"))
        self.assertFalse(Adresa.objects.filter(uid=loser.uid).exists())
        osoba.refresh_from_db()
        self.assertEqual(osoba.adresa_id, winner.uid)

    def test_spoji_self_merge_flashes_error(self):
        a, _ = self._make_dup_pair()
        r = self.client.post(
            reverse(
                "spoji_adresu",
                kwargs={"loser_uid": a.uid, "winner_uid": a.uid},
            ),
            follow=True,
        )
        self.assertEqual(r.status_code, 200)
        # Ред није обрисан; приказана је порука о грешци.
        self.assertTrue(Adresa.objects.filter(uid=a.uid).exists())
        msgs = [m.message for m in r.context["messages"]]
        self.assertTrue(any("into itself" in m for m in msgs))

    def test_spoji_get_rejected_405(self):
        a, b = self._make_dup_pair()
        r = self.client.get(
            reverse(
                "spoji_adresu",
                kwargs={"loser_uid": a.uid, "winner_uid": b.uid},
            )
        )
        self.assertEqual(r.status_code, 405)

    def test_spoji_forbidden_for_non_admin(self):
        loser, winner = self._make_dup_pair()
        self.client.force_login(self.clerk)
        r = self.client.post(
            reverse(
                "spoji_adresu",
                kwargs={"loser_uid": loser.uid, "winner_uid": winner.uid},
            )
        )
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Adresa.objects.filter(uid=loser.uid).exists())
