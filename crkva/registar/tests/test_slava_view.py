"""Basic tests for the slava-households view (slava_view)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from kalendar.models import Slava

User = get_user_model()


class SlavaDomacinstvaViewTests(TestCase):
    """slava_view.slava_domacinstva — render + context partitioning."""

    @classmethod
    def setUpTestData(cls):
        cls.slava = Slava.objects.create(
            naziv="Тест слава",
            mesec=5,
            dan=15,
            pokretni=False,
        )

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)

    def test_renders_for_existing_slava(self):
        url = reverse("slava_detail", kwargs={"uid": self.slava.uid})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Тест слава")

    def test_returns_404_for_missing_uid(self):
        url = reverse("slava_detail", kwargs={"uid": 999_999})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

    def test_passes_count_in_context(self):
        url = reverse("slava_detail", kwargs={"uid": self.slava.uid})
        r = self.client.get(url)
        self.assertIn("count", r.context)
        self.assertEqual(r.context["count"], 0)

    def test_partitions_members_in_context(self):
        """Each household in the context should carry .zivi_clanovi +
        .preminuli_clanovi attrs set by the view."""
        url = reverse("slava_detail", kwargs={"uid": self.slava.uid})
        r = self.client.get(url)
        self.assertIn("domacinstva", r.context)
        for d in r.context["domacinstva"]:
            self.assertTrue(hasattr(d, "zivi_clanovi"))
            self.assertTrue(hasattr(d, "preminuli_clanovi"))
