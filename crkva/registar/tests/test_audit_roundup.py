"""Регресиони тестови за ситне исправке из аудита (#340)."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Osoba


class AuditRoundupTest(TestCase):
    def setUp(self):
        self.client = Client()
        user = get_user_model().objects.create_superuser(
            username="roundup", email="", password="x"
        )
        self.client.force_login(user)
        cache.clear()  # _get_registry_stats кешира по шеми

    def test_kalendar_invalid_month_404(self):
        """Невалидан месец (13) враћа 404, не 500 (#340)."""
        url = reverse("kalendar_mesec", kwargs={"year": 2026, "month": 13})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_kalendar_out_of_range_year_404(self):
        """Огромна година враћа 404, не 500 (#340)."""
        url = reverse("kalendar_mesec", kwargs={"year": 999999999, "month": 1})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_kalendar_valid_month_ok(self):
        """Валидан месец се и даље рендерује (200)."""
        url = reverse("kalendar_mesec", kwargs={"year": 2026, "month": 7})
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_parohijani_stat_counts_only_parohijani(self):
        """Насловна статистика „Парохијани" броји parohijan=True, не све особе (#340)."""
        Osoba.objects.create(ime="Пар", prezime="Охијан", parohijan=True)
        Osoba.objects.create(ime="Кум", prezime="Некипар", parohijan=False)
        resp = self.client.get(reverse("search_view"))
        stats = resp.context["stats"]
        self.assertEqual(
            stats["parohijani"], Osoba.objects.filter(parohijan=True).count()
        )
        self.assertLess(stats["parohijani"], Osoba.objects.count())
