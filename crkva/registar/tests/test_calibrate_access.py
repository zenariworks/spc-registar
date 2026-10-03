"""#376: калибрационе странице траже пријаву и улогу и кад је калибрација укључена.

`calibrate_krstenje` и `calibrate_vencanje` су заштићени са
`@tenant_role_required` (који укључује `@login_required`); ови тестови чувају
ту заштиту.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from tenants.models import Clanstvo, Uloga, Zakupac

User = get_user_model()

URLS = ("calibrate_krstenje", "calibrate_vencanje")


@override_settings(CALIBRATION_ENABLED=True)
class CalibrateAccessTests(TestCase):
    """Приступ калибрационим страницама по улози."""

    @classmethod
    def setUpTestData(cls):
        tenant = Zakupac.objects.get(schema_name="test_tenant")
        cls.kancelarija = User.objects.create_user(username="kanc-cal", password="x")
        Clanstvo.objects.create(
            korisnik=cls.kancelarija, parohija=tenant, uloga=Uloga.KANCELARIJA
        )
        cls.pregled = User.objects.create_user(username="pregled-cal", password="x")
        Clanstvo.objects.create(
            korisnik=cls.pregled, parohija=tenant, uloga=Uloga.PREGLED
        )

    def _client(self, user=None):
        client = Client()
        if user is not None:
            client.force_login(user)
        return client

    def test_anonymous_redirects_to_login(self):
        """Анонимни корисник иде на пријаву, страница се не приказује."""
        client = self._client()
        for name in URLS:
            with self.subTest(name=name):
                response = client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn("/prijava/", response["Location"])

    def test_role_without_write_access_forbidden(self):
        """Улога „Преглед“ (само читање) добија 403."""
        client = self._client(self.pregled)
        for name in URLS:
            with self.subTest(name=name):
                self.assertEqual(client.get(reverse(name)).status_code, 403)

    def test_kancelarija_can_open(self):
        """Канцеларија (уписује крштења и венчања) отвара обе странице."""
        client = self._client(self.kancelarija)
        for name in URLS:
            with self.subTest(name=name):
                self.assertEqual(client.get(reverse(name)).status_code, 200)
