"""Tests for the slava-domacinstva page address rendering and dark-mode CSS."""

import pathlib

from django.test import TestCase
from django.urls import reverse
from registar.models import Adresa, Domacinstvo, Osoba, Slava


class SlavaAddressRenderTest(TestCase):
    """The slava domacinstva list must render the full address (not just the broj)."""

    @classmethod
    def setUpTestData(cls):
        cls.slava = Slava.objects.create(naziv="Никољдан", mesec=12, dan=19)
        cls.adresa = Adresa.objects.create(
            ulica="Поручника Спасића и Машере", broj="12", mesto="Чукарица"
        )
        cls.domacin = Osoba.objects.create(
            ime="Драган", prezime="Станчић", parohijan=True
        )
        Domacinstvo.objects.create(
            domacin=cls.domacin, adresa=cls.adresa, slava=cls.slava
        )

    def test_address_renders_full_text(self):
        """The list must include the street name, not only the broj."""
        response = self.client.get(
            reverse("slava_detail", kwargs={"uid": self.slava.uid})
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("Поручника Спасића и Машере", body)
        self.assertIn("12", body)
        self.assertIn("Чукарица", body)


class SlavaDarkModeCSSTest(TestCase):
    """Surface-level guards: hard-coded gray hex tokens should not be used for theme-sensitive surfaces."""

    def test_u_info_header_uses_theme_token(self):
        """.u-info-header background must come from the theme token, not a hex literal."""
        css = pathlib.Path(
            "crkva/registar/static/registar/components/kartice.css"
        ).read_text(encoding="utf-8")
        info_block = css.split(".u-info-header")[1].split("}")[0]
        self.assertIn("var(--color-surface-2)", info_block)
        self.assertNotIn("var(--color-gray-800)", info_block)

    def test_u_chip_muted_uses_theme_token(self):
        """.u-chip--muted background must come from the theme token."""
        css = pathlib.Path(
            "crkva/registar/static/registar/components/oznake.css"
        ).read_text(encoding="utf-8")
        chip_block = css.split(".u-chip--muted")[1].split("}")[0]
        self.assertIn("var(--color-surface-2)", chip_block)
        self.assertNotIn("var(--color-gray-800)", chip_block)
