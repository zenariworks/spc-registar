"""Regression tests for template-syntax leaking into rendered HTML.

The ``_modal_osoba.html`` partial originally opened with a multi-line
``{# ... #}`` Django comment. The ``{# ... #}`` form is single-line only,
so the parser never matched the closing ``#}`` and emitted the comment
markers as literal text near the bottom of every page that included the
partial -- ``/izmena/krstenje/<uid>/``, ``/izmena/vencanje/<uid>/``,
``/unos/krstenje/`` and ``/unos/vencanje/``.

These tests render those pages with a logged-in clerk and assert that no
raw template tokens (``{#``, ``#}``, ``{%``, ``%}``, ``{{``, ``}}``) appear
in the response body. They also render ``_modal_osoba.html`` directly so
a regression in the partial is caught even if the include points change.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from __future__ import annotations

import datetime

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Krstenje, Vencanje
from tenants.models import Clanstvo, Uloga, Zakupac

User = get_user_model()


TEMPLATE_TOKENS = ("{#", "#}", "{%", "%}", "{{", "}}")


def assert_no_template_tokens(testcase, body: str, *, where: str) -> None:
    """Fail loudly if any Django template token leaked into ``body``.

    We keep ``{%`` / ``%}`` in the list even though they're the most common
    legitimate tag markers because they MUST never appear in *rendered*
    output -- the template engine always strips them.
    """
    for token in TEMPLATE_TOKENS:
        testcase.assertNotIn(
            token,
            body,
            msg=f"{where}: raw template token {token!r} leaked into HTML",
        )


class ModalOsobaPartialRendersCleanlyTests(TestCase):
    """The partial itself must not leak template tokens when rendered alone.

    This guards against any future re-introduction of multi-line ``{# #}``
    comments or stray ``{%``/``{{`` typos at the top of the file.
    """

    def test_partial_renders_without_leaking_template_tokens(self):
        body = render_to_string("_partials/_modal_osoba.html")
        assert_no_template_tokens(self, body, where="_modal_osoba.html (direct render)")

    def test_partial_does_not_render_modal_component_doc_string(self):
        """The original bug surfaced this exact substring -- pin it."""
        body = render_to_string("_partials/_modal_osoba.html")
        self.assertNotIn("Uses the generic Modal component", body)
        self.assertNotIn("registar/components/modali.css", body)


class IncludingPagesDoNotLeakTemplateTokensTests(TestCase):
    """Pages that include ``_modal_osoba.html`` must render cleanly end-to-end."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Zakupac.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc-leak", password="x")
        Clanstvo.objects.create(
            korisnik=cls.clerk, parohija=cls.tenant, uloga=Uloga.KANCELARIJA
        )
        cls.krstenje = Krstenje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 2, 10),
            zivorodjeno=True,
            vanbracno=False,
            blizanac=False,
            telesna_mana=False,
        )
        cls.vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 1),
            razresenje=False,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)

    def _assert_clean(self, url_name: str, **kwargs) -> None:
        url = reverse(url_name, **kwargs)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200, msg=f"{url} returned {response.status_code}"
        )
        body = response.content.decode("utf-8")
        assert_no_template_tokens(self, body, where=url)
        # Pin the exact substring that the original bug leaked.
        self.assertNotIn("Uses the generic Modal component", body)

    def test_izmena_vencanje_does_not_leak(self):
        self._assert_clean("izmena_vencanja", kwargs={"uid": self.vencanje.uid})

    def test_izmena_krstenje_does_not_leak(self):
        self._assert_clean("izmena_krstenja", kwargs={"uid": self.krstenje.uid})

    def test_unos_krstenja_does_not_leak(self):
        self._assert_clean("unos_krstenja")

    def test_unos_vencanja_does_not_leak(self):
        self._assert_clean("unos_vencanja")
