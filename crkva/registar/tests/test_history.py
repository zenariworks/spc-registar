"""Tests for the history helper and per-page history panel."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from registar.history import history_for
from registar.models import Osoba, Svestenik
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class HistoryHelperTests(TestCase):
    """Verifies history_for() returns ordered entries with diffs."""

    def test_returns_empty_for_brand_new_instance(self):
        # In SQLite/Postgres tests, simple-history fires on save(); after a single
        # save there is one history record (no diff).
        o = Osoba.objects.create(ime="Тест", prezime="Један", pol="М")
        entries = history_for(o)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].record.history_type, "+")
        self.assertEqual(entries[0].changes, [])

    def test_returns_two_entries_after_update(self):
        o = Osoba.objects.create(ime="Тест", prezime="Два", pol="М")
        o.prezime = "Промењено"
        o.save()
        entries = history_for(o)
        self.assertEqual(len(entries), 2)
        # newest first
        self.assertEqual(entries[0].record.history_type, "~")
        # the update entry should diff against the create
        field_names = [c.field for c in entries[0].changes]
        self.assertIn("prezime", field_names)

    def test_returns_entries_for_svestenik_too(self):
        # PR 6 also added HistoricalRecords to Svestenik
        s = Svestenik.objects.create(ime="Пера", prezime="Пера", zvanje="јереј")
        s.zvanje = "протојереј"
        s.save()
        entries = history_for(s)
        self.assertEqual(len(entries), 2)
        changes = entries[0].changes
        self.assertTrue(any(c.field == "zvanje" for c in changes))


class HistoryPanelTemplateTests(TestCase):
    """Detail pages should embed the history panel."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.viewer = User.objects.create_user(username="view", password="x")
        UserMembership.objects.create(
            user=cls.viewer, tenant=cls.tenant, role=Role.PREGLED
        )
        cls.osoba = Osoba.objects.create(ime="Историја", prezime="Тест", pol="М")
        cls.osoba.prezime = "Тест2"
        cls.osoba.save()

    def setUp(self):
        self.client = Client()

    def test_parohijan_detail_includes_history_panel(self):
        self.client.force_login(self.viewer)
        r = self.client.get(f"/parohijan/{self.osoba.uid}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Историја измена")
        self.assertIn("history_entries", r.context)
        self.assertEqual(len(r.context["history_entries"]), 2)
