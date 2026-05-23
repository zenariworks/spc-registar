"""Regression tests for the select2 closed-state pill + inline create-osoba.

The /unos/vencanje/ page rendered raw native <select>s because
`{{ form.media.js }}` was emitted inside the `content` block, ABOVE the
jQuery <script> at the bottom of base.html. select2.full.min.js then
referenced an undefined `jQuery` global, the widgets were never wrapped,
and the new closed-state pill chrome from select2_skin.css never
applied. The "+ Додај нову особу" footer (injected by osoba_create.js on
`select2:open`) also never fired because that event is dispatched by
select2 — which never initialised.

This module pins the fix in three layers:

1. Script ordering on entry pages: jQuery → modal.js → select2.full.min.js
   → django_select2.js → osoba_create.js.
2. Per-widget HTML attrs on the Родитељи fieldset (svekar/svekrva/tast/
   tasta) and Krstenje (otac/majka): django-select2 class +
   data-minimum-input-length=0 + data-osoba-create=1.
3. CSS scope: select2_skin.css carries the closed-state pill rule that
   matches whatever select2 wraps around the underlying <select>.
"""

import datetime
import pathlib

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Krstenje, Vencanje


def _idx(html: str, needle: str) -> int:
    """Return the byte offset of the first occurrence of `needle` in `html`."""
    found = html.find(needle)
    assert found >= 0, f"Expected to find {needle!r} in rendered page"
    return found


# ---------------------------------------------------------------------------
# /unos/vencanje/ — the exact URL the user reported.
# ---------------------------------------------------------------------------


class UnosVencanjaSelect2InitTests(TestCase):
    """Render /unos/vencanje/ and assert select2 init prerequisites."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="venc-tester", email="t@x.test", password="x"
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def _get_html(self):
        response = self.client.get(reverse("unos_vencanja"))
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8")

    def test_page_loads_jquery_and_select2_scripts(self):
        """jQuery, select2.full.min.js, django_select2.js + osoba_create.js."""
        html = self._get_html()
        self.assertIn("jquery", html.lower())
        self.assertIn("select2.full.min.js", html)
        self.assertIn("django_select2/django_select2.js", html)
        self.assertIn("osoba_create.js", html)

    def test_jquery_loads_before_select2_scripts(self):
        """jQuery's <script> must precede select2.full.min.js + django_select2.js.

        Otherwise the IIFE in django_select2.js (`factory(jQuery || ...)`)
        throws ReferenceError before any widget is wrapped.
        """
        html = self._get_html()
        jquery_idx = _idx(html, "jquery-3.7.1.min.js")
        select2_idx = _idx(html, "select2.full.min.js")
        django_select2_idx = _idx(html, "django_select2/django_select2.js")
        self.assertLess(
            jquery_idx, select2_idx, "jQuery must precede select2.full.min.js"
        )
        self.assertLess(
            jquery_idx, django_select2_idx, "jQuery must precede django_select2.js"
        )

    def test_select2_loads_before_osoba_create(self):
        """osoba_create.js must run AFTER select2 is registered.

        It binds `.on('select2:open.osobaCreate', ...)` on every
        `select[data-osoba-create]`; that event is emitted by select2,
        so select2 must already be loaded for the binding to be useful.
        """
        html = self._get_html()
        select2_idx = _idx(html, "select2.full.min.js")
        django_select2_idx = _idx(html, "django_select2/django_select2.js")
        osoba_create_idx = _idx(html, "osoba_create.js")
        self.assertLess(
            select2_idx,
            osoba_create_idx,
            "select2.full.min.js must precede osoba_create.js",
        )
        self.assertLess(
            django_select2_idx,
            osoba_create_idx,
            "django_select2.js must precede osoba_create.js",
        )

    def test_roditelji_selects_carry_django_select2_class(self):
        """svekar/svekrva/tast/tasta keep the django-select2 init hook."""
        html = self._get_html()
        for name in ("svekar", "svekrva", "tast", "tasta"):
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=f"<select name={name!r}> must carry the django-select2 class",
            )

    def test_roditelji_selects_have_minimum_input_length_zero(self):
        """Suggestions show on click (min-input-length=0) for all four parents."""
        html = self._get_html()
        for name in ("svekar", "svekrva", "tast", "tasta"):
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*data-minimum-input-length="0"',
                msg=f"<select name={name!r}> must set data-minimum-input-length=0",
            )

    def test_every_osoba_fk_has_osoba_create_hook(self):
        """The inline + Додај нову особу hook must reach every Osoba FK."""
        html = self._get_html()
        # Every Osoba FK on the Vencanje form
        for name in (
            "zenik",
            "nevesta",
            "kum",
            "stari_svat",
            "svekar",
            "svekrva",
            "tast",
            "tasta",
        ):
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*data-osoba-create="1"',
                msg=f"<select name={name!r}> must opt into osoba_create.js",
            )


# ---------------------------------------------------------------------------
# /unos/krstenje/ — shares the same template wiring.
# ---------------------------------------------------------------------------


class UnosKrstenjaSelect2InitTests(TestCase):
    """Same prerequisites for /unos/krstenje/."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="krst-tester2", email="t@x.test", password="x"
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def _get_html(self):
        r = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(r.status_code, 200)
        return r.content.decode("utf-8")

    def test_jquery_loads_before_select2_scripts(self):
        html = self._get_html()
        self.assertLess(
            _idx(html, "jquery-3.7.1.min.js"), _idx(html, "select2.full.min.js")
        )

    def test_select2_loads_before_osoba_create(self):
        html = self._get_html()
        self.assertLess(
            _idx(html, "select2.full.min.js"), _idx(html, "osoba_create.js")
        )

    def test_osoba_create_js_referenced(self):
        """osoba_create.js must appear on /unos/krstenje/."""
        self.assertIn("osoba_create.js", self._get_html())

    def test_otac_majka_have_osoba_create_hook(self):
        html = self._get_html()
        for name in ("otac", "majka"):
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*data-osoba-create="1"',
            )


# ---------------------------------------------------------------------------
# /izmena/krstenje/<uid>/ — known-working edit page from the user report.
# ---------------------------------------------------------------------------


class IzmenaKrstenjeSelect2InitTests(TestCase):
    """Render /izmena/krstenje/<uid>/ and assert select2 init prerequisites."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="izm-krst", email="t@x.test", password="x"
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

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def _get_html(self):
        r = self.client.get(
            reverse("izmena_krstenja", kwargs={"uid": self.krstenje.uid})
        )
        self.assertEqual(r.status_code, 200)
        return r.content.decode("utf-8")

    def test_jquery_loads_before_select2_scripts(self):
        html = self._get_html()
        self.assertLess(
            _idx(html, "jquery-3.7.1.min.js"), _idx(html, "select2.full.min.js")
        )

    def test_select2_loads_before_osoba_create(self):
        html = self._get_html()
        self.assertLess(
            _idx(html, "select2.full.min.js"), _idx(html, "osoba_create.js")
        )

    def test_osoba_create_js_referenced(self):
        self.assertIn("osoba_create.js", self._get_html())


# ---------------------------------------------------------------------------
# /izmena/vencanje/<uid>/ — symmetric guard for edit page.
# ---------------------------------------------------------------------------


class IzmenaVencanjaSelect2InitTests(TestCase):
    """Render /izmena/vencanje/<uid>/ and assert select2 init prerequisites."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="izm-venc", email="t@x.test", password="x"
        )
        cls.vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 1),
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def _get_html(self):
        r = self.client.get(
            reverse("izmena_vencanja", kwargs={"uid": self.vencanje.uid})
        )
        self.assertEqual(r.status_code, 200)
        return r.content.decode("utf-8")

    def test_jquery_loads_before_select2_scripts(self):
        html = self._get_html()
        self.assertLess(
            _idx(html, "jquery-3.7.1.min.js"), _idx(html, "select2.full.min.js")
        )

    def test_select2_loads_before_osoba_create(self):
        html = self._get_html()
        self.assertLess(
            _idx(html, "select2.full.min.js"), _idx(html, "osoba_create.js")
        )

    def test_roditelji_selects_have_osoba_create_hook(self):
        html = self._get_html()
        for name in ("svekar", "svekrva", "tast", "tasta"):
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*data-osoba-create="1"',
            )


# ---------------------------------------------------------------------------
# CSS scope: the skin file targets the structure select2 actually emits.
# ---------------------------------------------------------------------------


class Select2SkinTargetsClosedStatePillTests(TestCase):
    """Pin the CSS selector that paints the closed-state pill chrome.

    Once select2 wraps a `.django-select2` <select> it emits

        .select2-container--default
          .select2-selection--single
            .select2-selection__rendered

    Our skin rules must target that structure across every page, not be
    scoped to a specific fieldset, or the Родитељи widgets render with
    the default ugly grey border (the user's reported symptom).
    """

    SKIN = pathlib.Path("crkva/registar/static/registar/components/select2_skin.css")

    def setUp(self):
        self.text = self.SKIN.read_text(encoding="utf-8")

    def test_closed_pill_selector_present(self):
        self.assertIn(
            ".select2-container--default .select2-selection--single",
            self.text,
            "select2_skin.css must target the closed-state pill",
        )

    def test_rendered_inner_selector_present(self):
        self.assertIn(
            ".select2-selection__rendered",
            self.text,
            "select2_skin.css must target the inner label area",
        )

    def test_skin_is_globally_scoped(self):
        """No `.info-page` or fieldset scope leaked into the skin selectors.

        select2 portals its dropdown to <body>, and the selection box
        lives wherever the widget is rendered. The skin must therefore
        be globally scoped (no parent class qualifier) so it applies on
        /unos/* and /izmena/* and /parohija/users/* alike.
        """
        for parent in (".info-page ", ".form ", ".form-section "):
            self.assertNotIn(
                parent + ".select2-container",
                self.text,
                f"select2_skin.css must not gate rules behind {parent!r}",
            )

    def test_skin_referenced_by_base_template(self):
        """The base template must keep the skin in the compressed bundle."""
        base = pathlib.Path("crkva/registar/templates/base.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("components/select2_skin.css", base)
