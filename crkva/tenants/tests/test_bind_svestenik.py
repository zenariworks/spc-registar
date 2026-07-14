"""#278: везивање корисничког налога за свештенички профил са /parohija/users/."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Svestenik
from tenants.models import Clanstvo, Uloga, Zakupac

User = get_user_model()


class BindSvestenikTests(TestCase):
    """Везивање/одвезивање корисника и свештеника + приказ на листи."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Zakupac.objects.get(schema_name="test_tenant")
        cls.admin = User.objects.create_user(username="adm", password="x")
        Clanstvo.objects.create(
            korisnik=cls.admin, parohija=cls.tenant, uloga=Uloga.ADMIN
        )
        cls.priest_user = User.objects.create_user(username="pop", password="x")
        Clanstvo.objects.create(
            korisnik=cls.priest_user, parohija=cls.tenant, uloga=Uloga.SVESTENSTVO
        )
        cls.sv1 = Svestenik.objects.create(
            ime="Марко", prezime="Марковић", zvanje="јереј"
        )
        cls.sv2 = Svestenik.objects.create(ime="Лука", prezime="Лукић", zvanje="јереј")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    def _bind_url(self, user):
        return reverse("parohija:user_bind_svestenik", kwargs={"user_id": user.pk})

    def test_non_admin_forbidden(self):
        self.client.force_login(self.priest_user)
        r = self.client.post(
            self._bind_url(self.priest_user), {"svestenik": self.sv1.uid}
        )
        self.assertEqual(r.status_code, 403)

    def test_admin_binds_user_to_priest(self):
        r = self.client.post(
            self._bind_url(self.priest_user), {"svestenik": self.sv1.uid}
        )
        self.assertEqual(r.status_code, 302)
        self.sv1.refresh_from_db()
        self.assertEqual(self.sv1.user_id, self.priest_user.pk)

    def test_clear_binding(self):
        self.sv1.user = self.priest_user
        self.sv1.save(update_fields=["user"])
        r = self.client.post(self._bind_url(self.priest_user), {"svestenik": ""})
        self.assertEqual(r.status_code, 302)
        self.sv1.refresh_from_db()
        self.assertIsNone(self.sv1.user_id)

    def test_rebinding_moves_link_off_previous_priest(self):
        self.sv1.user = self.priest_user
        self.sv1.save(update_fields=["user"])
        self.client.post(self._bind_url(self.priest_user), {"svestenik": self.sv2.uid})
        self.sv1.refresh_from_db()
        self.sv2.refresh_from_db()
        self.assertIsNone(self.sv1.user_id)
        self.assertEqual(self.sv2.user_id, self.priest_user.pk)

    def test_cannot_steal_priest_bound_to_another_user(self):
        other = User.objects.create_user(username="drugi", password="x")
        self.sv1.user = other
        self.sv1.save(update_fields=["user"])
        r = self.client.post(
            self._bind_url(self.priest_user), {"svestenik": self.sv1.uid}
        )
        self.assertEqual(r.status_code, 302)
        self.sv1.refresh_from_db()
        self.assertEqual(self.sv1.user_id, other.pk)

    def test_list_shows_warning_when_unbound(self):
        r = self.client.get(reverse("parohija:korisnici"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "није везан")

    def test_list_shows_priest_when_bound(self):
        self.sv1.user = self.priest_user
        self.sv1.save(update_fields=["user"])
        r = self.client.get(reverse("parohija:korisnici"))
        self.assertContains(r, str(self.sv1))
