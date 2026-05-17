"""Tests for the izmena_* edit views."""

# pylint: disable=missing-function-docstring

import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Domacinstvo, Krstenje, Osoba, Svestenik, Vencanje
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class IzmenaParohijanaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.priest = User.objects.create_user(username="svest", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.osoba = Osoba.objects.create(ime="Стари", prezime="Тест", pol="М")

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("izmena_parohijana", kwargs={"uid": self.osoba.uid})

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_clerk_can_open_and_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        r2 = self.client.post(
            self.url(),
            {"ime": "Нови", "prezime": "Тест", "pol": "М"},
        )
        self.assertEqual(r2.status_code, 302)
        self.osoba.refresh_from_db()
        self.assertEqual(self.osoba.ime, "Нови")

    def test_priest_cannot_open(self):
        self.client.force_login(self.priest)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 403)

    def test_unknown_uid_404(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("izmena_parohijana", kwargs={"uid": 999999}))
        self.assertEqual(r.status_code, 404)

    def test_pol_radio_has_checked_for_male(self):
        """Edit form must mark the saved Пол radio as checked (data-loss guard)."""
        self.osoba.pol = "М"
        self.osoba.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        # The selected radio for М must include `checked`.
        self.assertContains(r, 'name="pol" value="М" checked')
        # The other choice must NOT be checked.
        self.assertNotContains(r, 'name="pol" value="Ж" checked')

    def test_pol_radio_has_checked_for_female(self):
        self.osoba.pol = "Ж"
        self.osoba.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'name="pol" value="Ж" checked')
        self.assertNotContains(r, 'name="pol" value="М" checked')


class IzmenaSvestenikaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.priest = User.objects.create_user(username="svest", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.svestenik = Svestenik.objects.create(
            ime="Стари", prezime="Свештеник", zvanje="Јереј"
        )

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("izmena_svestenika", kwargs={"uid": self.svestenik.uid})

    def test_priest_can_edit(self):
        self.client.force_login(self.priest)
        r = self.client.post(
            self.url(),
            {"ime": "Стари", "prezime": "Свештеник", "zvanje": "Протојереј"},
        )
        self.assertEqual(r.status_code, 302)
        self.svestenik.refresh_from_db()
        self.assertEqual(self.svestenik.zvanje, "Протојереј")

    def test_clerk_cannot_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 403)


class IzmenaDomacinstvaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.domacin = Osoba.objects.create(ime="Стефан", prezime="Стефан", pol="М")
        cls.domacinstvo = Domacinstvo.objects.create(domacin=cls.domacin)

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("izmena_domacinstva", kwargs={"uid": self.domacinstvo.uid})

    def test_clerk_can_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            self.url(),
            {
                "domacin": str(self.domacin.uid),
                "napomena": "промењено",
                "slavska_vodica": "on",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.domacinstvo.refresh_from_db()
        self.assertEqual(self.domacinstvo.napomena, "промењено")
        self.assertTrue(self.domacinstvo.slavska_vodica)

    def test_slavska_vodica_checkbox_checked_when_true(self):
        """Edit form must render slavska_vodica checked when DB value is True."""
        self.domacinstvo.slavska_vodica = True
        self.domacinstvo.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        # Look for `name="slavska_vodica"` with `checked` attribute.
        self.assertContains(r, 'name="slavska_vodica"')
        self.assertContains(r, 'name="slavska_vodica" id="id_slavska_vodica" checked')

    def test_vaskrsnja_vodica_checkbox_checked_when_true(self):
        self.domacinstvo.vaskrsnja_vodica = True
        self.domacinstvo.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(
            r, 'name="vaskrsnja_vodica" id="id_vaskrsnja_vodica" checked'
        )

    def test_vodice_unchecked_when_false(self):
        """When False, the checkbox MUST NOT carry `checked` (would silently re-arm)."""
        self.domacinstvo.slavska_vodica = False
        self.domacinstvo.vaskrsnja_vodica = False
        self.domacinstvo.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(
            r, 'name="slavska_vodica" id="id_slavska_vodica" checked'
        )
        self.assertNotContains(
            r, 'name="vaskrsnja_vodica" id="id_vaskrsnja_vodica" checked'
        )


class IzmenaKrstenjaTests(TestCase):
    """Edit-form rendering for Krstenje — every BooleanField must round-trip."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()

    def _create_krstenje(self, **overrides):
        defaults = dict(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 2, 10),
            dete_rodjeno_zivo=True,
            dete_vanbracno=True,
            dete_blizanac=True,
            dete_sa_telesnom_manom=True,
        )
        defaults.update(overrides)
        return Krstenje.objects.create(**defaults)

    def url(self, k):
        return reverse("izmena_krstenja", kwargs={"uid": k.uid})

    def test_all_bool_fields_render_checked_when_true(self):
        """Every BooleanField on Krstenje must render `checked` when DB is True."""
        k = self._create_krstenje()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(k))
        self.assertEqual(r.status_code, 200)
        for fname in [
            "dete_rodjeno_zivo",
            "dete_vanbracno",
            "dete_blizanac",
            "dete_sa_telesnom_manom",
        ]:
            self.assertContains(
                r,
                f'name="{fname}" id="id_{fname}" checked',
                msg_prefix=f"{fname} should be checked",
            )

    def test_all_bool_fields_unchecked_when_false(self):
        k = self._create_krstenje(
            dete_rodjeno_zivo=False,
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(k))
        self.assertEqual(r.status_code, 200)
        for fname in [
            "dete_rodjeno_zivo",
            "dete_vanbracno",
            "dete_blizanac",
            "dete_sa_telesnom_manom",
        ]:
            self.assertNotContains(
                r,
                f'name="{fname}" id="id_{fname}" checked',
                msg_prefix=f"{fname} should NOT be checked",
            )

    def test_mixed_bool_state_renders_per_field(self):
        """Mixed True/False on the same record renders each independently."""
        k = self._create_krstenje(
            dete_rodjeno_zivo=True,
            dete_vanbracno=False,
            dete_blizanac=True,
            dete_sa_telesnom_manom=False,
        )
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(k))
        self.assertContains(
            r, 'name="dete_rodjeno_zivo" id="id_dete_rodjeno_zivo" checked'
        )
        self.assertNotContains(
            r, 'name="dete_vanbracno" id="id_dete_vanbracno" checked'
        )
        self.assertContains(r, 'name="dete_blizanac" id="id_dete_blizanac" checked')
        self.assertNotContains(
            r, 'name="dete_sa_telesnom_manom" id="id_dete_sa_telesnom_manom" checked'
        )


class IzmenaVencanjaTests(TestCase):
    """Edit-form rendering for Vencanje — razresenje BooleanField round-trip."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()

    def _create_vencanje(self, **overrides):
        defaults = dict(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 1),
            razresenje=True,
        )
        defaults.update(overrides)
        return Vencanje.objects.create(**defaults)

    def url(self, v):
        return reverse("izmena_vencanja", kwargs={"uid": v.uid})

    def test_razresenje_checked_when_true(self):
        v = self._create_vencanje(razresenje=True)
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(v))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'name="razresenje" id="id_razresenje" checked')

    def test_razresenje_not_checked_when_false(self):
        v = self._create_vencanje(razresenje=False)
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(v))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'name="razresenje" id="id_razresenje" checked')
