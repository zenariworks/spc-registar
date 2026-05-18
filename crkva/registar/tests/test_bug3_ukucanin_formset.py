"""Regression: укућана мора бити могуће додати/уклонити кроз izmena_domacinstva."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Domacinstvo, Osoba, Ukucanin
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class UkucaninFormsetTests(TestCase):
    """Bug 3: укућана мора бити могуће додати/уклонити кроз izmena_domacinstva."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.domacin = Osoba.objects.create(
            ime="Домаћин", prezime="Тест", pol="М", parohijan=True
        )
        cls.member = Osoba.objects.create(
            ime="Члан", prezime="Тест", pol="Ж", parohijan=True
        )
        cls.domacinstvo = Domacinstvo.objects.create(domacin=cls.domacin)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)

    def url(self):
        return reverse("izmena_domacinstva", kwargs={"uid": self.domacinstvo.uid})

    def _base_payload(self):
        return {
            "domacin": str(self.domacin.uid),
            "slavska_vodica": "off",
            "vaskrsnja_vodica": "off",
        }

    def test_edit_page_renders_ukucanin_formset(self):
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "ukucani-TOTAL_FORMS")
        self.assertContains(r, "ukucani-INITIAL_FORMS")

    def test_post_adds_ukucanin_row(self):
        self.assertEqual(self.domacinstvo.ukucani.count(), 0)
        payload = self._base_payload()
        payload.update(
            {
                "ukucani-TOTAL_FORMS": "1",
                "ukucani-INITIAL_FORMS": "0",
                "ukucani-MIN_NUM_FORMS": "0",
                "ukucani-MAX_NUM_FORMS": "1000",
                "ukucani-0-osoba": str(self.member.uid),
                "ukucani-0-ime_ukucana": "",
                "ukucani-0-uloga": "дете",
                "ukucani-0-preminuo": "",
            }
        )
        r = self.client.post(self.url(), payload)
        self.assertEqual(r.status_code, 302, msg=r.content.decode()[:500])
        self.assertEqual(self.domacinstvo.ukucani.count(), 1)
        u = self.domacinstvo.ukucani.first()
        self.assertEqual(u.osoba_id, self.member.uid)
        self.assertEqual(u.uloga, "дете")

    def test_post_deletes_ukucanin_row(self):
        u = Ukucanin.objects.create(
            domacinstvo=self.domacinstvo, osoba=self.member, uloga="дете"
        )
        payload = self._base_payload()
        payload.update(
            {
                "ukucani-TOTAL_FORMS": "1",
                "ukucani-INITIAL_FORMS": "1",
                "ukucani-MIN_NUM_FORMS": "0",
                "ukucani-MAX_NUM_FORMS": "1000",
                "ukucani-0-id": str(u.pk),
                "ukucani-0-domacinstvo": str(self.domacinstvo.uid),
                "ukucani-0-osoba": str(self.member.uid),
                "ukucani-0-ime_ukucana": "",
                "ukucani-0-uloga": "дете",
                "ukucani-0-preminuo": "",
                "ukucani-0-DELETE": "on",
            }
        )
        r = self.client.post(self.url(), payload)
        self.assertEqual(r.status_code, 302, msg=r.content.decode()[:500])
        self.assertEqual(self.domacinstvo.ukucani.count(), 0)

    def test_existing_post_without_formset_still_works(self):
        """Legacy POST without management form must still be accepted."""
        r = self.client.post(self.url(), self._base_payload())
        self.assertEqual(r.status_code, 302, msg=r.content.decode()[:500])
