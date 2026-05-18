"""Tests for the inline Adresa edit modal on the Domacinstvo edit page.

Covers:
- The pencil button + #adresa-modal render in the edit-mode template.
- The brzi_izmena_adrese endpoint updates the existing row in place.
- The endpoint requires authentication and the domacinstvo role.
- Boolean toggles render as slider-styled checkboxes (Bug 2 markup).
- View mode renders the booleans as "Да" / "Не".
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Adresa, Domacinstvo, Osoba
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class _BaseDomacinstvoMixin:
    @classmethod
    def _make_users_and_household(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc-adr", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.priest = User.objects.create_user(username="svest-adr", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.domacin = Osoba.objects.create(ime="Адр", prezime="Тест", pol="М")
        cls.adresa = Adresa.objects.create(
            ulica="Стара", broj="1", broj_stana="", mesto="Београд"
        )
        cls.domacinstvo = Domacinstvo.objects.create(
            domacin=cls.domacin, adresa=cls.adresa
        )


class AdresaEditMarkupTests(_BaseDomacinstvoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._make_users_and_household()

    def setUp(self):
        self.client = Client()
        self.url = reverse(
            "izmena_domacinstva", kwargs={"uid": self.domacinstvo.uid}
        )

    def test_adresa_edit_button_renders_on_domacinstvo_edit_page(self):
        """The Adresa select2 carries the data attribute the JS hooks into."""
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        # The form widget exposes the hook attribute consumed by adresa_edit.js
        # so the JS can mount the pencil button next to the select.
        self.assertContains(r, 'data-adresa-edit="1"')

    def test_adresa_edit_modal_in_dom(self):
        """The inline-edit modal markup is present on the edit page."""
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="adresa-modal"')
        self.assertContains(r, 'id="modal-adresa-ulica"')
        self.assertContains(r, 'id="modal-adresa-broj"')
        self.assertContains(r, 'id="modal-adresa-broj_stana"')
        self.assertContains(r, 'id="modal-adresa-mesto"')

    def test_adresa_edit_js_loaded(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        self.assertContains(r, "adresa_edit.js")

    def test_initial_adresa_payload_in_dom(self):
        """JSON block carries the currently-linked address so the modal can
        pre-fill its inputs without an extra round-trip."""
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        self.assertContains(r, 'id="adresa-modal-initial"')
        self.assertContains(r, '"ulica": "Стара"')
        self.assertContains(r, '"mesto": "Београд"')

    def test_adresa_select_preselects_current_household_address(self):
        """The Adresa <select> renders the household's current adresa as the
        initial selected option (Bug 1a)."""
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        body = r.content.decode("utf-8")
        # find the <select name="adresa" ...> ... </select> block
        start = body.find('name="adresa"')
        self.assertGreater(start, -1)
        end = body.find("</select>", start)
        self.assertGreater(end, start)
        block = body[start:end]
        # The matching <option> for the saved uid must carry `selected`.
        self.assertIn(str(self.adresa.uid), block)
        # And the option carrying that uid must be marked selected.
        self.assertIn("selected", block)


class AdresaEditEndpointTests(_BaseDomacinstvoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._make_users_and_household()

    def setUp(self):
        self.client = Client()
        self.url = reverse(
            "brzi_izmena_adrese", kwargs={"uid": self.adresa.uid}
        )

    def test_endpoint_updates_existing_row(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            self.url,
            {
                "ulica": "Нова",
                "broj": "42",
                "broj_stana": "3А",
                "mesto": "Нови Сад",
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], str(self.adresa.uid))
        self.adresa.refresh_from_db()
        self.assertEqual(self.adresa.ulica, "Нова")
        self.assertEqual(self.adresa.broj, "42")
        self.assertEqual(self.adresa.broj_stana, "3А")
        self.assertEqual(self.adresa.mesto, "Нови Сад")

    def test_endpoint_returns_refreshed_label(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            self.url,
            {
                "ulica": "Краља",
                "broj": "7",
                "broj_stana": "",
                "mesto": "Београд",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("Краља", r.json()["text"])

    def test_endpoint_requires_auth_anonymous_redirects(self):
        r = self.client.post(
            self.url, {"ulica": "x", "broj": "1", "broj_stana": "", "mesto": "y"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_endpoint_requires_domacinstvo_role(self):
        self.client.force_login(self.priest)
        r = self.client.post(
            self.url,
            {"ulica": "x", "broj": "1", "broj_stana": "", "mesto": "y"},
        )
        self.assertEqual(r.status_code, 403)
        # Row must remain untouched.
        self.adresa.refresh_from_db()
        self.assertEqual(self.adresa.ulica, "Стара")

    def test_endpoint_get_rejected(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 405)

    def test_endpoint_404_for_missing_uid(self):
        self.client.force_login(self.clerk)
        import uuid as _uuid

        bogus = reverse("brzi_izmena_adrese", kwargs={"uid": _uuid.uuid4()})
        r = self.client.post(bogus, {"ulica": "x"})
        self.assertEqual(r.status_code, 404)


class VodicaSliderToggleMarkupTests(_BaseDomacinstvoMixin, TestCase):
    """Bug 2: slavska_vodica / vaskrsnja_vodica must render as slider toggles.

    The slider CSS in info.css targets
    ``.info-row--editable .info-row__value > input[type="checkbox"]`` so the
    checkbox MUST be a direct child of ``.info-row__value`` (i.e. not wrapped
    in a <label>) for the slider style to apply.
    """

    @classmethod
    def setUpTestData(cls):
        cls._make_users_and_household()

    def setUp(self):
        self.client = Client()
        self.url = reverse(
            "izmena_domacinstva", kwargs={"uid": self.domacinstvo.uid}
        )

    def _editable_value_block(self, html, field_name):
        marker = f'name="{field_name}"'
        idx = html.find(marker)
        self.assertGreater(idx, -1, f"{field_name} not in rendered HTML")
        # Look back for the enclosing info-row__value div.
        start = html.rfind('info-row__value', 0, idx)
        self.assertGreater(start, -1)
        end = html.find('</li>', idx)
        return html[start:end]

    def test_slavska_vodica_renders_as_slider_toggle(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        html = r.content.decode("utf-8")
        block = self._editable_value_block(html, "slavska_vodica")
        # Slider styling requires the checkbox to be a direct child of
        # info-row__value, NOT nested inside a <label>.
        # Check that the <input> immediately follows the opening tag.
        self.assertIn('info-row__value">', block)
        # Specifically: no <label>...<input>...</label> wrap.
        label_idx = block.find("<label")
        input_idx = block.find("<input")
        self.assertGreater(input_idx, -1)
        if label_idx > -1:
            self.assertGreater(
                label_idx,
                input_idx,
                "label must come AFTER the checkbox so the checkbox is a "
                "direct child of info-row__value (slider CSS requirement).",
            )

    def test_vaskrsnja_vodica_renders_as_slider_toggle(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        html = r.content.decode("utf-8")
        block = self._editable_value_block(html, "vaskrsnja_vodica")
        label_idx = block.find("<label")
        input_idx = block.find("<input")
        self.assertGreater(input_idx, -1)
        if label_idx > -1:
            self.assertGreater(label_idx, input_idx)

    def test_editable_row_class_present_for_both_vodica_fields(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url)
        html = r.content.decode("utf-8")
        for field in ("slavska_vodica", "vaskrsnja_vodica"):
            block = self._editable_value_block(html, field)
            # The <li> wrapper must carry info-row--editable.
            self.assertIn("info-row--editable", html[: html.find(block)])

    def test_view_mode_shows_da_for_true_bools(self):
        self.domacinstvo.slavska_vodica = True
        self.domacinstvo.vaskrsnja_vodica = True
        self.domacinstvo.save()
        self.client.force_login(self.clerk)
        r = self.client.get(
            reverse("domacinstvo_detail", kwargs={"uid": self.domacinstvo.uid})
        )
        self.assertEqual(r.status_code, 200)
        body = r.content.decode("utf-8")
        self.assertIn("Славска водица: Да", body)
        self.assertIn("Васкршња водица: Да", body)

    def test_view_mode_shows_ne_for_false_bools(self):
        self.domacinstvo.slavska_vodica = False
        self.domacinstvo.vaskrsnja_vodica = False
        self.domacinstvo.save()
        self.client.force_login(self.clerk)
        r = self.client.get(
            reverse("domacinstvo_detail", kwargs={"uid": self.domacinstvo.uid})
        )
        self.assertEqual(r.status_code, 200)
        body = r.content.decode("utf-8")
        self.assertIn("Славска водица: Не", body)
        self.assertIn("Васкршња водица: Не", body)
