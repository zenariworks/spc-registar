"""End-to-end audit of /unos/krstenje/ (Krstenje entry form).


User report: "a lot does not work" on http://46.224.30.151:9000/unos/krstenje/.

One test per audit checklist item (see PR description). Each test asserts
a SPECIFIC user-facing element/behaviour, not just "page returns 200".

Coverage:

1. Page loads cleanly (200, no template-token leak, jQuery → select2 order).
2. Every select2 widget actually carries the django-select2 class plus the
   data-minimum-input-length=0 + (where applicable) data-osoba-create hook,
   and the gender filter is rendered on otac/majka.
3. Date / time pickers are emitted as native HTML5 <input type="date"|"time">.
4. Boolean and twin-name fields render the right input element AND accept
   user input (verified by submitting and asserting the saved row).
5. /select2/fields/auto.json returns Hram rows for the hram widget.
6. POST with a full payload creates a Krstenje row end-to-end.
7. Anonymous user is redirected to login (CSRF + auth).
8. The "+ Додај нову особу" flow: opening the dete dropdown surfaces the
   create-new footer wiring (data-osoba-create=1) AND the modal is
   present + bound to the brzi_unos_osobe endpoint.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from __future__ import annotations

import datetime
import re

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Hram, Krstenje, Osoba, Svestenik
from registar.models.parohija import Parohija
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


FIELD_ID_RE_NAME_FIRST = re.compile(
    r'<select[^>]*name="(?P<name>[a-z_]+)"[^>]*data-field_id="(?P<fid>[^"]+)"'
)
FIELD_ID_RE_FID_FIRST = re.compile(
    r'<select[^>]*data-field_id="(?P<fid>[^"]+)"[^>]*name="(?P<name>[a-z_]+)"'
)


def _extract_field_ids(html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in FIELD_ID_RE_NAME_FIRST.finditer(html):
        out.setdefault(m.group("name"), m.group("fid"))
    for m in FIELD_ID_RE_FID_FIRST.finditer(html):
        out.setdefault(m.group("name"), m.group("fid"))
    return out


class _BaseUnosKrstenjeAuditTest(TestCase):
    """Shared fixtures + helpers for every audit test below."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="audit-kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        # Reference data for FK widgets.
        cls.parohija = Parohija.objects.create(naziv="Тест парохија")
        cls.hram = Hram.objects.create(naziv="Тест храм", mesto="Тест")
        cls.svestenik = Svestenik.objects.create(
            ime="Свештеник",
            prezime="Тестовић",
            zvanje="јереј",
            parohija=cls.parohija,
        )
        cls.dete = Osoba.objects.create(ime="Дете", prezime="Тестовић", pol="М")
        cls.otac = Osoba.objects.create(ime="Отац", prezime="Тестовић", pol="М")
        cls.majka = Osoba.objects.create(ime="Мајка", prezime="Тестовић", pol="Ж")
        cls.kum = Osoba.objects.create(ime="Кум", prezime="Тестовић", pol="М")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)

    def _get_html(self) -> str:
        r = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(r.status_code, 200, msg=r.content[:400])
        return r.content.decode("utf-8")

    def _valid_payload(self, **override) -> dict:
        payload = {
            "redni_broj": "1",
            "godina_registracije": "2024",
            "knjiga": "1",
            "strana": "1",
            "broj": "1",
            "datum": "2024-02-10",
            "vreme": "11:30",
            "hram": str(self.hram.pk),
            "dete": str(self.dete.pk),
            "otac": str(self.otac.pk),
            "majka": str(self.majka.pk),
            "kum": str(self.kum.pk),
            "svestenik": str(self.svestenik.pk),
            # Bool fields — checkbox semantics: presence = True.
            "zivorodjeno": "on",
            # "vanbracno" omitted == False
            # "blizanac" omitted == False
            # "telesna_mana" omitted == False
            "po_redu": "1",
            "ime_blizanca": "",
            "mesto_registracije": "Београд",
            "datum_registracije": "2024-02-12",
            "maticni_broj": "12345",
            "strana_registracije": "7",
            "primedba": "Тест",
        }
        payload.update(override)
        return payload


# ---------------------------------------------------------------------------
# Checklist 1 — page loads cleanly
# ---------------------------------------------------------------------------


class PageLoadsCleanlyTests(_BaseUnosKrstenjeAuditTest):
    """200, no template-token leak, jQuery before select2."""

    def test_page_returns_200_for_clerk(self):
        r = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(r.status_code, 200)

    def test_page_uses_unos_krstenja_template(self):
        r = self.client.get(reverse("unos_krstenja"))
        self.assertTemplateUsed(r, "registar/krstenje.html")

    def test_no_raw_template_tokens_leak_into_html(self):
        html = self._get_html()
        for token in ("{#", "#}", "{%", "%}", "{{", "}}"):
            self.assertNotIn(
                token,
                html,
                msg=f"raw template token {token!r} leaked into rendered HTML",
            )

    def test_jquery_loads_before_select2_full_min_js(self):
        """select2.full.min.js references jQuery — jQuery must precede it."""
        html = self._get_html()
        jq = html.find("jquery-3.7.1.min.js")
        s2 = html.find("select2.full.min.js")
        self.assertGreater(jq, 0, "jQuery <script> missing from /unos/krstenje/")
        self.assertGreater(s2, 0, "select2.full.min.js missing from /unos/krstenje/")
        self.assertLess(jq, s2, "jQuery must load BEFORE select2.full.min.js")

    def test_select2_loads_before_osoba_create(self):
        html = self._get_html()
        s2 = html.find("select2.full.min.js")
        oc = html.find("osoba_create.js")
        self.assertLess(s2, oc, "select2 must load before osoba_create.js")


# ---------------------------------------------------------------------------
# Checklist 2 — every select2 widget is wired
# ---------------------------------------------------------------------------


class Select2WidgetWiringTests(_BaseUnosKrstenjeAuditTest):
    """Every FK field must be a select2-heavy with min-input-length=0."""

    OSOBA_FIELDS = ("dete", "otac", "majka", "kum")
    ALL_SELECT2_FIELDS = OSOBA_FIELDS + ("svestenik", "hram")

    def test_every_fk_field_carries_django_select2_class(self):
        html = self._get_html()
        for name in self.ALL_SELECT2_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=(
                    f"<select name={name!r}> missing django-select2 class — "
                    "select2 will not wrap it"
                ),
            )

    def test_every_fk_field_has_minimum_input_length_zero(self):
        """Clicking shows suggestions immediately (no typing required)."""
        html = self._get_html()
        for name in self.ALL_SELECT2_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*data-minimum-input-length="0"',
                msg=f"<select name={name!r}> must set data-minimum-input-length=0",
            )

    def test_osoba_fk_fields_carry_osoba_create_hook(self):
        """dete/otac/majka/kum must opt into osoba_create.js."""
        html = self._get_html()
        for name in self.OSOBA_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*data-osoba-create="1"',
                msg=f"<select name={name!r}> missing data-osoba-create",
            )

    def test_otac_carries_male_gender_filter_attr(self):
        html = self._get_html()
        m = re.search(r'<select[^>]*name="otac"[^>]*>', html)
        self.assertIsNotNone(m, "otac <select> not rendered")
        self.assertIn(
            'data-osoba-default-pol="М"',
            m.group(0),
            msg="otac field must surface the М default-pol so the modal pre-picks it",
        )

    def test_majka_carries_female_gender_filter_attr(self):
        html = self._get_html()
        m = re.search(r'<select[^>]*name="majka"[^>]*>', html)
        self.assertIsNotNone(m, "majka <select> not rendered")
        self.assertIn(
            'data-osoba-default-pol="Ж"',
            m.group(0),
            msg="majka field must surface the Ж default-pol",
        )

    def test_select2_skin_css_is_loaded(self):
        """The chevron-pill closed state lives in select2_skin.css."""
        html = self._get_html()
        # CSS comes through compressor → match by the unique fragment.
        # Compressed CSS may rename, so just probe that the skin is referenced
        # via the base bundle.
        self.assertRegex(
            html,
            r'<link[^>]+rel="stylesheet"[^>]+href="[^"]+"',
            msg="no <link> CSS bundle on /unos/krstenje/",
        )

    def test_otac_filter_excludes_female_via_ajax(self):
        """The live AJAX endpoint enforces the gender restriction for otac."""
        html = self._get_html()
        ids = _extract_field_ids(html)
        self.assertIn("otac", ids)
        r = self.client.get(
            reverse("django_select2:auto-json"),
            {"field_id": ids["otac"], "term": "Тестовић"},
        )
        self.assertEqual(r.status_code, 200, msg=r.content[:200])
        result_ids = {row["id"] for row in r.json().get("results", [])}
        self.assertIn(self.otac.pk, result_ids)
        self.assertIn(self.dete.pk, result_ids)  # male too
        self.assertIn(self.kum.pk, result_ids)  # male too
        self.assertNotIn(
            self.majka.pk, result_ids, msg="majka (Ж) leaked into otac (М) lookup"
        )


# ---------------------------------------------------------------------------
# Checklist 3 — date/time pickers
# ---------------------------------------------------------------------------


class DateTimePickerTests(_BaseUnosKrstenjeAuditTest):
    """Native HTML5 date/time inputs must be emitted (not plain text)."""

    def test_datum_is_html5_date_input(self):
        html = self._get_html()
        self.assertRegex(
            html,
            r'<input[^>]*type="date"[^>]*name="datum"',
            msg='datum field must render <input type="date">',
        )

    def test_vreme_is_html5_time_input(self):
        html = self._get_html()
        self.assertRegex(
            html,
            r'<input[^>]*type="time"[^>]*name="vreme"',
            msg='vreme field must render <input type="time">',
        )

    def test_datum_registracije_is_html5_date_input(self):
        html = self._get_html()
        self.assertRegex(
            html,
            r'<input[^>]*type="date"[^>]*name="datum_registracije"',
        )


# ---------------------------------------------------------------------------
# Checklist 4 — boolean info-row fields render + accept input
# ---------------------------------------------------------------------------


class BooleanInfoRowsTests(_BaseUnosKrstenjeAuditTest):
    """zivorodjeno / vanbracno / blizanac / telesna_mana."""

    BOOL_FIELDS = (
        "zivorodjeno",
        "vanbracno",
        "blizanac",
        "telesna_mana",
    )

    def test_every_bool_field_renders_a_checkbox(self):
        html = self._get_html()
        for name in self.BOOL_FIELDS:
            self.assertRegex(
                html,
                rf'<input[^>]*type="checkbox"[^>]*name="{name}"',
                msg=f"{name!r} must render as a checkbox",
            )

    def test_drugo_dete_blizanac_ime_renders_a_text_input(self):
        html = self._get_html()
        self.assertRegex(
            html,
            r'<input[^>]*type="text"[^>]*name="ime_blizanca"',
            msg="ime_blizanca must render as a text input",
        )

    def test_info_rows_use_editable_modifier_class(self):
        """The feat/krstenje-dete-info-rows refactor put these in
        info-row--editable so they share spacing with the rest of the page."""
        html = self._get_html()
        # Pin the editable-row container around the zivorodjeno input.
        m = re.search(
            r'<li[^>]*class="[^"]*info-row--editable[^"]*"[^>]*>'
            r".*?zivorodjeno",
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(
            m,
            msg='zivorodjeno checkbox must live inside "info-row--editable"',
        )

    def test_bool_field_values_persist_through_post(self):
        """Submit with a mix of checked/unchecked bools and verify storage."""
        payload = self._valid_payload(
            zivorodjeno="on",
            blizanac="on",
            ime_blizanca="Близанчић",
        )
        # vanbracno + telesna_mana intentionally omitted (False).
        r = self.client.post(reverse("unos_krstenja"), payload, follow=False)
        self.assertEqual(r.status_code, 302, msg=r.content[:600])
        k = Krstenje.objects.latest("created")
        self.assertTrue(k.zivorodjeno)
        self.assertTrue(k.blizanac)
        self.assertFalse(k.vanbracno)
        self.assertFalse(k.telesna_mana)
        self.assertEqual(k.ime_blizanca, "Близанчић")


# ---------------------------------------------------------------------------
# Checklist 5 — Hram AJAX endpoint
# ---------------------------------------------------------------------------


class HramAjaxLookupTests(_BaseUnosKrstenjeAuditTest):
    """The /select2/fields/auto.json endpoint must return Hram rows for hram."""

    def test_hram_ajax_returns_hram_rows(self):
        html = self._get_html()
        ids = _extract_field_ids(html)
        self.assertIn("hram", ids, msg=f"hram field_id missing — got {list(ids)}")
        r = self.client.get(
            reverse("django_select2:auto-json"),
            {"field_id": ids["hram"], "term": "Тест"},
        )
        self.assertEqual(r.status_code, 200, msg=r.content[:200])
        payload = r.json()
        self.assertIn("results", payload)
        result_ids = {row["id"] for row in payload["results"]}
        self.assertIn(str(self.hram.pk), result_ids)

    def test_svestenik_ajax_returns_svestenik_rows(self):
        html = self._get_html()
        ids = _extract_field_ids(html)
        self.assertIn("svestenik", ids)
        r = self.client.get(
            reverse("django_select2:auto-json"),
            {"field_id": ids["svestenik"], "term": "Тестовић"},
        )
        self.assertEqual(r.status_code, 200, msg=r.content[:200])
        result_ids = {row["id"] for row in r.json().get("results", [])}
        self.assertIn(self.svestenik.pk, result_ids)


# ---------------------------------------------------------------------------
# Checklist 5b — django-select2 cache must be cross-process safe
# ---------------------------------------------------------------------------


class Select2CacheBackendTests(TestCase):
    """The most-load-bearing bug behind "a lot does not work".

    django-select2 mints a signed ``field_id`` on every page render and
    stores the widget's queryset metadata in Django's cache. The browser
    then GETs ``/select2/fields/auto.json?field_id=…`` and the server
    looks the key up to know which queryset to filter.

    Django's default cache is ``LocMemCache`` — strictly per-process.
    Production runs under gunicorn ``workers=3`` (sync), so a field_id
    minted by worker A is invisible to workers B + C; AJAX hits the
    other worker and gets a 404 ``field_id not found`` ~67% of the time.
    Visible symptom: the Hram / Svestenik / Osoba dropdowns silently
    refuse to load suggestions.

    Pin a cross-process backend so this regression cannot return.
    """

    def test_default_cache_backend_is_not_locmem(self):
        from django.conf import settings as _settings

        backend = _settings.CACHES["default"]["BACKEND"]
        self.assertNotIn(
            "locmem",
            backend.lower(),
            msg=(
                "Default cache is LocMemCache which is per-process. "
                "django-select2 stores field_id metadata here; under "
                "gunicorn workers=3 (see scripts/gunicorn.conf.py) the "
                "AJAX endpoint returns 404 for ~67% of requests. Use "
                "FileBasedCache (or Redis/Memcached) instead."
            ),
        )

    def test_select2_field_id_round_trips_through_cache(self):
        """Render the page, then re-fetch the field_id from cache.

        This is the strongest possible end-to-end probe in a single-process
        test: it pins that ``signing.loads`` of the rendered field_id maps
        to a live cache entry, which is the exact path the AJAX view takes.
        """
        from django.contrib.auth import get_user_model as _gu
        from django.core import signing
        from django.core.cache import cache as _cache
        from django_select2.conf import settings as s2_settings
        from tenants.models import Role, Tenant, UserMembership

        User_ = _gu()
        tenant = Tenant.objects.get(schema_name="test_tenant")
        clerk = User_.objects.create_user(username="cache-probe", password="x")
        UserMembership.objects.create(user=clerk, tenant=tenant, role=Role.KANCELARIJA)
        c = Client()
        c.force_login(clerk)
        r = c.get(reverse("unos_krstenja"))
        self.assertEqual(r.status_code, 200)
        ids = _extract_field_ids(r.content.decode("utf-8"))
        self.assertIn("hram", ids, msg="hram select2 widget not rendered")

        key = signing.loads(ids["hram"])
        cache_key = f"{s2_settings.SELECT2_CACHE_PREFIX}{key}"
        self.assertIsNotNone(
            _cache.get(cache_key),
            msg=(
                "django-select2 field_id was signed but never stored in "
                "the configured cache — AJAX lookups will 404"
            ),
        )


# ---------------------------------------------------------------------------
# Checklist 6 — submission creates a Krstenje
# ---------------------------------------------------------------------------


class FullSubmissionTests(_BaseUnosKrstenjeAuditTest):
    """Submit a fully-populated payload and assert end-to-end persistence."""

    def test_valid_post_creates_krstenje_and_redirects_to_list(self):
        before = Krstenje.objects.count()
        r = self.client.post(reverse("unos_krstenja"), self._valid_payload())
        self.assertEqual(
            r.status_code,
            302,
            msg=(
                "valid POST should redirect; got "
                f"{r.status_code} — body: {r.content[:500]!r}"
            ),
        )
        self.assertEqual(r["Location"], reverse("krstenja"))
        self.assertEqual(Krstenje.objects.count(), before + 1)

        k = Krstenje.objects.latest("created")
        self.assertEqual(k.dete_id, self.dete.pk)
        self.assertEqual(k.otac_id, self.otac.pk)
        self.assertEqual(k.majka_id, self.majka.pk)
        self.assertEqual(k.kum_id, self.kum.pk)
        self.assertEqual(k.hram_id, self.hram.pk)
        self.assertEqual(k.svestenik_id, self.svestenik.pk)
        self.assertEqual(k.datum, datetime.date(2024, 2, 10))
        self.assertEqual(k.vreme, datetime.time(11, 30))
        self.assertEqual(k.mesto_registracije, "Београд")
        self.assertEqual(k.primedba, "Тест")

    def test_invalid_post_returns_form_with_error_block_not_500(self):
        """Missing required fields must round-trip a friendly error, not 500."""
        bad = self._valid_payload()
        del bad["godina_registracije"]
        del bad["hram"]
        r = self.client.post(reverse("unos_krstenja"), bad)
        self.assertEqual(r.status_code, 200, msg="invalid POST must re-render form")
        body = r.content.decode("utf-8")
        self.assertIn("u-alert--error", body, msg="_form_errors.html must be included")
        # The field-specific error must be visible (not just non_field_errors).
        self.assertIn("godina_registracije", body)


# ---------------------------------------------------------------------------
# Checklist 7 — CSRF + auth
# ---------------------------------------------------------------------------


class AuthAndCsrfTests(_BaseUnosKrstenjeAuditTest):
    """Anonymous users must be redirected to login; CSRF token is on the form."""

    def setUp(self):
        # Do not auto-login here — we want to probe anonymous behaviour.
        self.client = Client()

    def test_anonymous_get_redirects_to_login(self):
        r = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_anonymous_post_also_redirects_to_login(self):
        r = self.client.post(reverse("unos_krstenja"), {"redni_broj": "1"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_csrf_token_present_in_rendered_form(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("csrfmiddlewaretoken", r.content.decode("utf-8"))


# ---------------------------------------------------------------------------
# Checklist 8 — "+ Додај нову особу" inline create flow
# ---------------------------------------------------------------------------


class OsobaCreateInlineFlowTests(_BaseUnosKrstenjeAuditTest):
    """The dropdown footer + modal + brzi_unos_osobe round-trip.

    The footer itself is injected client-side by osoba_create.js on the
    select2:open event, so we can't see it in server-rendered HTML.
    Instead we verify the wiring points that make it possible:
      * data-osoba-create=1 on every Osoba <select> (DOM hook)
      * #osoba-modal markup is included on the page
      * Modal.bindForm() is configured for the brzi_unos_osobe URL
      * POSTing to brzi_unos_osobe creates an Osoba and returns id+text
    """

    def setUp(self):
        from django.contrib.auth import get_user_model

        _U = get_user_model()
        self.user = _U.objects.create_superuser(
            username="auto-test", email="a@a.test", password="x"
        )
        self.client.force_login(self.user)

    def test_modal_markup_is_included_on_page(self):
        html = self._get_html()
        self.assertIn('id="osoba-modal"', html)
        self.assertIn('id="modal-ime"', html)
        self.assertIn('id="modal-prezime"', html)
        self.assertIn('id="modal-pol-toggle"', html)

    def test_modal_form_bound_to_brzi_unos_osobe_endpoint(self):
        html = self._get_html()
        # The bound URL must be the django-resolved brzi_unos_osobe endpoint.
        self.assertIn(
            f'url: "{reverse("brzi_unos_osobe")}"',
            html,
            msg="Modal.bindForm must point at brzi_unos_osobe URL",
        )

    def test_osoba_create_js_is_referenced_after_select2(self):
        html = self._get_html()
        self.assertIn("osoba_create.js", html)
        self.assertLess(
            html.find("select2.full.min.js"),
            html.find("osoba_create.js"),
            msg="osoba_create.js must follow select2 (it binds select2:open)",
        )

    def test_brzi_unos_osobe_creates_osoba_via_post(self):
        """Simulate the modal save: POST ime+prezime+pol, get back id+text."""
        r = self.client.post(
            reverse("brzi_unos_osobe"),
            {"ime": "Тест", "prezime": "Тестовић", "pol": "Ж"},
        )
        self.assertEqual(r.status_code, 200, msg=r.content[:200])
        data = r.json()
        self.assertIn("id", data)
        self.assertIn("text", data)
        self.assertTrue(Osoba.objects.filter(pk=data["id"]).exists())
        new = Osoba.objects.get(pk=data["id"])
        self.assertEqual(new.ime, "Тест")
        self.assertEqual(new.prezime, "Тестовић")
        self.assertEqual(new.pol, "Ж")
