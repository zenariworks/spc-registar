"""Test that /parohijani/ only shows Osobe with parohijan=True."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Osoba

User = get_user_model()


class SpisakParohijanaFiltersByParohijanFlag(TestCase):
    """The list page is named 'парохијани' — must not include parohijan=False Osobe."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)
        Osoba.objects.create(ime="Парохијан", prezime="Прави", parohijan=True)
        Osoba.objects.create(ime="Мати", prezime="Из крштења", parohijan=False)
        Osoba.objects.create(
            ime="Биљана", prezime="", devojacko_prezime="Томић", parohijan=False
        )

    def test_list_includes_only_parohijani(self):
        response = self.client.get(reverse("parohijani"))
        body = response.content.decode()
        self.assertIn("Парохијан Прави", body)
        self.assertNotIn("Мати Из крштења", body)

    def test_orphan_with_blank_prezime_is_excluded(self):
        response = self.client.get(reverse("parohijani"))
        body = response.content.decode()
        # The "Биљана" with parohijan=False and no surname must NOT leak in
        self.assertNotIn(">Биљана<", body)
