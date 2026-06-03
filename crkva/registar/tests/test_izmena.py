"""Tests for the izmena_* edit views."""

# pylint: disable=missing-function-docstring

import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Domacinstvo, Krstenje, Osoba, Svestenik, Vencanje
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class IzmenaParohijanaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.priest = User.objects.create_user(username="svest", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.osoba = Osoba.objects.create(ime="Стари", prezime="Тест", pol="М")

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("izmena_parohijana", kwargs={"uid": self.osoba.uid})

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_clerk_can_open_and_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        r2 = self.client.post(
            self.url(),
            {"ime": "Нови", "prezime": "Тест", "pol": "М"},
        )
        self.assertEqual(r2.status_code, 302)
        self.osoba.refresh_from_db()
        self.assertEqual(self.osoba.ime, "Нови")

    def test_priest_cannot_open(self):
        self.client.force_login(self.priest)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 403)

    def test_unknown_uid_404(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("izmena_parohijana", kwargs={"uid": 999999}))
        self.assertEqual(r.status_code, 404)

    def test_pol_radio_has_checked_for_male(self):
        """Edit form must mark the saved Пол radio as checked (data-loss guard)."""
        self.osoba.pol = "М"
        self.osoba.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        # The selected radio for М must include `checked`.
        self.assertContains(r, 'name="pol" value="М" checked')
        # The other choice must NOT be checked.
        self.assertNotContains(r, 'name="pol" value="Ж" checked')

    def test_pol_radio_has_checked_for_female(self):
        self.osoba.pol = "Ж"
        self.osoba.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'name="pol" value="Ж" checked')
        self.assertNotContains(r, 'name="pol" value="М" checked')


class IzmenaSvestenikaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.priest = User.objects.create_user(username="svest", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.svestenik = Svestenik.objects.create(
            ime="Стари", prezime="Свештеник", zvanje="јереј"
        )

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("izmena_svestenika", kwargs={"uid": self.svestenik.uid})

    def test_priest_can_edit(self):
        self.client.force_login(self.priest)
        r = self.client.post(
            self.url(),
            {"ime": "Стари", "prezime": "Свештеник", "zvanje": "протојереј"},
        )
        self.assertEqual(r.status_code, 302)
        self.svestenik.refresh_from_db()
        self.assertEqual(self.svestenik.zvanje, "протојереј")

    def test_clerk_cannot_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 403)


class IzmenaDomacinstvaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.domacin = Osoba.objects.create(ime="Стефан", prezime="Стефан", pol="М")
        cls.domacinstvo = Domacinstvo.objects.create(domacin=cls.domacin)

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("izmena_domacinstva", kwargs={"uid": self.domacinstvo.uid})

    def test_clerk_can_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            self.url(),
            {
                "domacin": str(self.domacin.uid),
                "napomena": "промењено",
                "slavska_vodica": "on",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.domacinstvo.refresh_from_db()
        self.assertEqual(self.domacinstvo.napomena, "промењено")
        self.assertTrue(self.domacinstvo.slavska_vodica)

    def test_slavska_vodica_checkbox_checked_when_true(self):
        """Edit form must render slavska_vodica checked when DB value is True."""
        self.domacinstvo.slavska_vodica = True
        self.domacinstvo.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        # Look for `name="slavska_vodica"` with `checked` attribute.
        self.assertContains(r, 'name="slavska_vodica"')
        self.assertContains(r, 'name="slavska_vodica" id="id_slavska_vodica" checked')

    def test_vaskrsnja_vodica_checkbox_checked_when_true(self):
        self.domacinstvo.vaskrsnja_vodica = True
        self.domacinstvo.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(
            r, 'name="vaskrsnja_vodica" id="id_vaskrsnja_vodica" checked'
        )

    def test_vodice_unchecked_when_false(self):
        """When False, the checkbox MUST NOT carry `checked` (would silently re-arm)."""
        self.domacinstvo.slavska_vodica = False
        self.domacinstvo.vaskrsnja_vodica = False
        self.domacinstvo.save()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(
            r, 'name="slavska_vodica" id="id_slavska_vodica" checked'
        )
        self.assertNotContains(
            r, 'name="vaskrsnja_vodica" id="id_vaskrsnja_vodica" checked'
        )


class IzmenaKrstenjaTests(TestCase):
    """Edit-form rendering for Krstenje — every BooleanField must round-trip."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()

    def _create_krstenje(self, **overrides):
        defaults = dict(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 2, 10),
            zivorodjeno=True,
            vanbracno=True,
            blizanac=True,
            telesna_mana=True,
        )
        defaults.update(overrides)
        return Krstenje.objects.create(**defaults)

    def url(self, k):
        return reverse("izmena_krstenja", kwargs={"uid": k.uid})

    def test_all_bool_fields_render_checked_when_true(self):
        """Every BooleanField on Krstenje must render `checked` when DB is True."""
        k = self._create_krstenje()
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(k))
        self.assertEqual(r.status_code, 200)
        for fname in [
            "zivorodjeno",
            "vanbracno",
            "blizanac",
            "telesna_mana",
        ]:
            self.assertContains(
                r,
                f'name="{fname}" id="id_{fname}" checked',
                msg_prefix=f"{fname} should be checked",
            )

    def test_all_bool_fields_unchecked_when_false(self):
        k = self._create_krstenje(
            zivorodjeno=False,
            vanbracno=False,
            blizanac=False,
            telesna_mana=False,
        )
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(k))
        self.assertEqual(r.status_code, 200)
        for fname in [
            "zivorodjeno",
            "vanbracno",
            "blizanac",
            "telesna_mana",
        ]:
            self.assertNotContains(
                r,
                f'name="{fname}" id="id_{fname}" checked',
                msg_prefix=f"{fname} should NOT be checked",
            )

    def test_mixed_bool_state_renders_per_field(self):
        """Mixed True/False on the same record renders each independently."""
        k = self._create_krstenje(
            zivorodjeno=True,
            vanbracno=False,
            blizanac=True,
            telesna_mana=False,
        )
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(k))
        self.assertContains(
            r, 'name="zivorodjeno" id="id_dete_rodjeno_zivo" checked'
        )
        self.assertNotContains(
            r, 'name="vanbracno" id="id_dete_vanbracno" checked'
        )
        self.assertContains(r, 'name="blizanac" id="id_dete_blizanac" checked')
        self.assertNotContains(
            r, 'name="telesna_mana" id="id_dete_sa_telesnom_manom" checked'
        )

    def test_dete_bool_fields_use_info_row_editable_markup(self):
        """Each Дете bool/text field must render as its own info-row--editable."""
        k = self._create_krstenje(
            zivorodjeno=True,
            vanbracno=False,
            blizanac=True,
            telesna_mana=False,
            ime_blizanca="Лука",
        )
        self.client.force_login(self.clerk)
        html = self.client.get(self.url(k)).content.decode("utf-8")
        # No leftover plain-label wrappers from the old form-row layout
        # (lowercase model-verbose-name labels).
        self.assertNotIn("<label>{0}".format("<input"), html)
        self.assertNotIn("ванбрачно</label>", html)
        # Each field is wrapped in its own .info-row.info-row--editable list
        # item with the matching tooltip on .info-row__icon.
        expected_tooltips = [
            "Дете рођено живо",
            "Дете по реду (по мајци)",
            "Ванбрачно дете",
            "Дете близанац",
            "Име другог детета близанца",
            "Дете са телесном маном",
        ]
        for tooltip in expected_tooltips:
            # Use a relaxed marker so trailing whitespace / attribute ordering
            # variations between Django versions don't break the assertion.
            needle = f'data-tooltip="{tooltip}"'
            self.assertIn(
                needle,
                html,
                msg=f'Missing data-tooltip for "{tooltip}"',
            )
            # And verify the row that hosts the icon is an info-row--editable.
            idx = html.index(needle)
            preceding = html[max(0, idx - 200) : idx]
            self.assertIn(
                "info-row info-row--editable",
                preceding,
                msg=(
                    f"Row hosting tooltip {tooltip!r} should carry "
                    f"info-row--editable; preceding 200 chars: {preceding!r}"
                ),
            )

    def test_dete_bool_widgets_are_bare_checkboxes(self):
        """Bool widgets render as bare <input type=checkbox> (slider style).

        The slider-toggle CSS in info.css targets
        ``.info-row--editable .info-row__value > input[type="checkbox"]`` —
        so the checkbox MUST be a direct child of ``.info-row__value``,
        not nested deeper. This guards against regressions where the
        widget gets wrapped in an extra div / label.
        """
        k = self._create_krstenje()
        self.client.force_login(self.clerk)
        html = self.client.get(self.url(k)).content.decode("utf-8")
        for fname in (
            "zivorodjeno",
            "vanbracno",
            "blizanac",
            "telesna_mana",
        ):
            self.assertIn(
                f'<input type="checkbox" name="{fname}"',
                html,
                msg=f"{fname} should render as bare <input type=checkbox>",
            )
            idx = html.index(f'<input type="checkbox" name="{fname}"')
            preceding = html[max(0, idx - 200) : idx]
            self.assertIn(
                'class="info-row__value"',
                preceding,
                msg=(
                    f"{fname} checkbox must sit directly inside .info-row__value "
                    f"so the slider-toggle CSS applies; "
                    f"preceding 200 chars: {preceding!r}"
                ),
            )


class PrikazKrstenjaDeteSectionTests(TestCase):
    """View-mode (is_edit=False) rendering of the Дете bool fields."""

    def setUp(self):
        self.client = Client()
        from django.contrib.auth import get_user_model

        _U = get_user_model()
        self.user = _U.objects.create_superuser(
            username="auto-test", email="a@a.test", password="x"
        )
        self.client.force_login(self.user)

    def _create_krstenje(self, **overrides):
        defaults = dict(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 2, 10),
            zivorodjeno=True,
            vanbracno=False,
            blizanac=True,
            telesna_mana=False,
            ime_blizanca="Лука",
        )
        defaults.update(overrides)
        return Krstenje.objects.create(**defaults)

    def url(self, k):
        return reverse("krstenje_detail", kwargs={"uid": k.uid})

    def test_view_mode_shows_da_ne_for_each_bool(self):
        """View mode must render Да/Не values for every dete bool."""
        k = self._create_krstenje()
        html = self.client.get(self.url(k)).content.decode("utf-8")
        # Each bool field has its own info-row with the right tooltip; the
        # static (view-mode) text is rendered via .info-row__static, which
        # in the unified template lives inline with the label.
        cases = [
            ("Дете рођено живо", "Да"),
            ("Ванбрачно дете", "Не"),
            ("Дете близанац", "Да"),
            ("Дете са телесном маном", "Не"),
        ]
        for tooltip, expected in cases:
            row_marker = f'<div class="info-row__icon" data-tooltip="{tooltip}">'
            self.assertIn(row_marker, html, msg=f'No row for "{tooltip}"')
            idx = html.index(row_marker)
            static_open = html.index('<span class="info-row__static">', idx)
            static_close = html.index("</span>", static_open)
            value_html = html[static_open:static_close]
            self.assertIn(
                expected,
                value_html,
                msg=f'Expected "{expected}" inside {tooltip} static, got: {value_html!r}',
            )

    def test_view_mode_shows_twin_sibling_name_when_blizanac(self):
        """If blizanac is true, ime_blizanca is shown beside it."""
        k = self._create_krstenje(blizanac=True, ime_blizanca="Лука")
        r = self.client.get(self.url(k))
        self.assertContains(r, "Лука")

    def test_view_mode_renders_false_bools_as_ne(self):
        """All four bools set to False render Не (not omitted)."""
        k = self._create_krstenje(
            zivorodjeno=False,
            vanbracno=False,
            blizanac=False,
            telesna_mana=False,
        )
        html = self.client.get(self.url(k)).content.decode("utf-8")
        for tooltip in (
            "Дете рођено живо",
            "Ванбрачно дете",
            "Дете близанац",
            "Дете са телесном маном",
        ):
            row_marker = f'<div class="info-row__icon" data-tooltip="{tooltip}">'
            self.assertIn(row_marker, html)
            static_open = html.index(
                '<span class="info-row__static">', html.index(row_marker)
            )
            static_close = html.index("</span>", static_open)
            self.assertIn("Не", html[static_open:static_close])


class InfoCssRulesTests(TestCase):
    """Smoke-test that the info-section / info-row CSS rules are present."""

    def test_info_css_defines_section_and_editable_row(self):
        import pathlib

        from django.conf import settings

        css_path = (
            pathlib.Path(settings.BASE_DIR)
            / "registar"
            / "static"
            / "registar"
            / "components"
            / "info.css"
        )
        content = css_path.read_text(encoding="utf-8")
        self.assertIn(".info-section", content)
        self.assertIn(".info-row--editable", content)
        # The slider styling that gives bool checkboxes the toggle look must
        # also be present so the Дете section renders correctly.
        self.assertIn(
            '.info-row--editable .info-row__value > input[type="checkbox"]',
            content,
        )


class IzmenaVencanjaTests(TestCase):
    """Edit-form rendering for Vencanje — razresenje BooleanField round-trip."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()

    def _create_vencanje(self, **overrides):
        defaults = dict(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 1),
            razresenje=True,
        )
        defaults.update(overrides)
        return Vencanje.objects.create(**defaults)

    def url(self, v):
        return reverse("izmena_vencanja", kwargs={"uid": v.uid})

    def test_razresenje_checked_when_true(self):
        v = self._create_vencanje(razresenje=True)
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(v))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'name="razresenje" id="id_razresenje" checked')

    def test_razresenje_not_checked_when_false(self):
        v = self._create_vencanje(razresenje=False)
        self.client.force_login(self.clerk)
        r = self.client.get(self.url(v))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'name="razresenje" id="id_razresenje" checked')
