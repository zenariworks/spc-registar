"""#376: калибрационе странице траже пријаву и улогу и кад је калибрација укључена.

`calibrate_krstenje` и `calibrate_vencanje` су заштићени са
`@tenant_role_required` (који укључује `@login_required`); ови тестови чувају
ту заштиту.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from tenants.models import Clanstvo, Uloga, Zakupac

Korisnik = get_user_model()

STRANICE = ("calibrate_krstenje", "calibrate_vencanje")


@override_settings(CALIBRATION_ENABLED=True)
class CalibrateAccessTests(TestCase):
    """Приступ калибрационим страницама по улози."""

    @classmethod
    def setUpTestData(cls):
        parohija = Zakupac.objects.get(schema_name="test_tenant")
        cls.kancelarija = Korisnik.objects.create_user(
            username="kanc-cal", password="x"
        )
        Clanstvo.objects.create(
            korisnik=cls.kancelarija, parohija=parohija, uloga=Uloga.KANCELARIJA
        )
        cls.pregled = Korisnik.objects.create_user(username="pregled-cal", password="x")
        Clanstvo.objects.create(
            korisnik=cls.pregled, parohija=parohija, uloga=Uloga.PREGLED
        )

    def _klijent(self, korisnik=None):
        klijent = Client()
        if korisnik is not None:
            klijent.force_login(korisnik)
        return klijent

    def test_anonymous_redirects_to_login(self):
        """Анонимни корисник иде на пријаву, страница се не приказује."""
        klijent = self._klijent()
        for stranica in STRANICE:
            with self.subTest(stranica=stranica):
                odgovor = klijent.get(reverse(stranica))
                self.assertEqual(odgovor.status_code, 302)
                self.assertIn("/prijava/", odgovor["Location"])

    def test_role_without_write_access_forbidden(self):
        """Улога „Преглед“ (само читање) добија 403."""
        klijent = self._klijent(self.pregled)
        for stranica in STRANICE:
            with self.subTest(stranica=stranica):
                self.assertEqual(klijent.get(reverse(stranica)).status_code, 403)

    def test_kancelarija_can_open(self):
        """Канцеларија (уписује крштења и венчања) отвара обе странице."""
        klijent = self._klijent(self.kancelarija)
        for stranica in STRANICE:
            with self.subTest(stranica=stranica):
                self.assertEqual(klijent.get(reverse(stranica)).status_code, 200)
