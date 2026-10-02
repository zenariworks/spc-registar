"""Све гране разрешавања парохије у SessionTenantMiddleware._resolve_tenant."""

# pylint: disable=protected-access

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from tenants.middleware import SESSION_TENANT_KEY, SessionTenantMiddleware
from tenants.models import Clanstvo, Uloga, Zakupac

User = get_user_model()


class ResolveTenantGraneTests(TestCase):
    """Сесија, чланство и подразумевана парохија, тим редом."""

    @classmethod
    def setUpTestData(cls):
        cls.podrazumevana = Zakupac.objects.get(schema_name="test_tenant")
        Zakupac.objects.bulk_create(
            [
                Zakupac(schema_name="test_grane_a", naziv="А", is_active=True),
                Zakupac(schema_name="test_grane_b", naziv="Б", is_active=True),
                Zakupac(schema_name="test_grane_x", naziv="Х", is_active=False),
            ]
        )
        cls.a = Zakupac.objects.get(schema_name="test_grane_a")
        cls.b = Zakupac.objects.get(schema_name="test_grane_b")
        cls.neaktivna = Zakupac.objects.get(schema_name="test_grane_x")
        cls.user = User.objects.create_user(username="grane", password="x")

    def zahtev(self, user, session=None, sa_sesijom=True):
        """GET захтев са корисником и (опционо) сесијом као речником."""
        request = RequestFactory().get("/")
        request.user = user
        if sa_sesijom:
            request.session = dict(session or {})
        return request

    def clan(self, parohija, **polja):
        """Чланство корисника у парохији."""
        return Clanstvo.objects.create(
            korisnik=self.user, parohija=parohija, uloga=Uloga.PREGLED, **polja
        )

    def test_session_tenant_with_membership_is_kept(self):
        """Парохија из сесије са активним чланством остаје, уз то чланство."""
        clanstvo = self.clan(self.a)
        self.clan(self.b, is_default=True)
        req = self.zahtev(self.user, {SESSION_TENANT_KEY: self.a.pk})
        self.assertEqual(
            SessionTenantMiddleware._resolve_tenant(req), (self.a, clanstvo)
        )
        self.assertEqual(req.session[SESSION_TENANT_KEY], self.a.pk)

    def test_inactive_session_tenant_is_evicted(self):
        """Неактивна парохија у сесији се избацује; следи чланство."""
        clanstvo = self.clan(self.a)
        req = self.zahtev(self.user, {SESSION_TENANT_KEY: self.neaktivna.pk})
        self.assertEqual(
            SessionTenantMiddleware._resolve_tenant(req), (self.a, clanstvo)
        )
        self.assertEqual(req.session[SESSION_TENANT_KEY], self.a.pk)

    def test_default_membership_is_preferred(self):
        """Међу активним чланствима бира се подразумевано."""
        self.clan(self.a)
        clanstvo = self.clan(self.b, is_default=True)
        req = self.zahtev(self.user)
        self.assertEqual(
            SessionTenantMiddleware._resolve_tenant(req), (self.b, clanstvo)
        )

    def test_membership_in_inactive_tenant_is_ignored(self):
        """Чланство у неактивној парохији не води у њу."""
        self.clan(self.neaktivna)
        req = self.zahtev(self.user)
        self.assertEqual(
            SessionTenantMiddleware._resolve_tenant(req), (self.podrazumevana, None)
        )

    def test_superuser_without_session_falls_back_to_default(self):
        """Суперкорисник без сесије и чланства иде у подразумевану парохију."""
        su = User.objects.create_superuser(username="grane-su", password="x")
        self.assertEqual(
            SessionTenantMiddleware._resolve_tenant(self.zahtev(su)),
            (self.podrazumevana, None),
        )

    def test_anonymous_user_gets_default_tenant(self):
        """Анониман корисник добија подразумевану парохију, без чланства."""
        req = self.zahtev(AnonymousUser(), {SESSION_TENANT_KEY: self.a.pk})
        self.assertEqual(
            SessionTenantMiddleware._resolve_tenant(req), (self.podrazumevana, None)
        )
        self.assertNotIn(SESSION_TENANT_KEY, req.session)

    def test_request_without_session(self):
        """Захтев без сесије и без корисника иде у подразумевану парохију."""
        request = RequestFactory().get("/")
        self.assertEqual(
            SessionTenantMiddleware._resolve_tenant(request),
            (self.podrazumevana, None),
        )

    def test_no_default_tenant_gives_none(self):
        """Без подразумеване парохије нема ни парохије ни чланства."""
        Zakupac.objects.filter(is_default=True).update(is_default=False)
        self.assertEqual(
            SessionTenantMiddleware._resolve_tenant(self.zahtev(self.user)),
            (None, None),
        )
