"""Tests asserting every ForeignKey field on every form renders with
the django-select2 init class.

The user wants every FK to be a typed-lookup (select2 with AJAX
suggestions), not a plain native <select>. The django-select2 init JS
hooks every `<select class="django-select2">` and replaces it with the
select2 dropdown, so every FK must carry that class on its <select>.
"""

# pylint: disable=missing-function-docstring

import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Krstenje, Vencanje


class _LoggedInAdminMixin:
    @classmethod
    def setUpTestData(cls):  # noqa: D401
        cls.user = User.objects.create_superuser(
            username=f"all-fk-{cls.__name__.lower()}",
            email="x@x.test",
            password="x",
        )

    def setUp(self):  # noqa: D401
        self.client = Client()
        self.client.force_login(self.user)


class KrstenjeFormFkSelect2Tests(_LoggedInAdminMixin, TestCase):
    """Every FK on KrstenjeForm renders as <select class="django-select2">."""

    FK_FIELDS = ("dete", "otac", "majka", "kum", "svestenik", "hram")

    def test_every_fk_select_carries_django_select2_class(self):
        r = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for name in self.FK_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=f"<select name={name!r}> on KrstenjeForm must be select2",
            )


class VencanjeFormFkSelect2Tests(_LoggedInAdminMixin, TestCase):
    """Every FK on VencanjeForm renders as <select class="django-select2">."""

    FK_FIELDS = (
        "zenik",
        "nevesta",
        "kum",
        "svekar",
        "svekrva",
        "tast",
        "tasta",
        "stari_svat",
        "svestenik",
        "hram",
    )

    def test_every_fk_select_carries_django_select2_class(self):
        r = self.client.get(reverse("unos_vencanja"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for name in self.FK_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=f"<select name={name!r}> on VencanjeForm must be select2",
            )


class ParohijanFormFkSelect2Tests(_LoggedInAdminMixin, TestCase):
    """Every FK on ParohijanForm renders as <select class="django-select2">."""

    FK_FIELDS = ("zanimanje", "veroispovest", "narodnost", "adresa")

    def test_every_fk_select_carries_django_select2_class(self):
        r = self.client.get(reverse("unos_parohijana"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for name in self.FK_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=f"<select name={name!r}> on ParohijanForm must be select2",
            )


class SvestenikFormFkSelect2Tests(_LoggedInAdminMixin, TestCase):
    """Every FK on SvestenikForm renders as <select class="django-select2">."""

    FK_FIELDS = ("parohija", "adresa")

    def test_every_fk_select_carries_django_select2_class(self):
        r = self.client.get(reverse("unos_svestenika"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for name in self.FK_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=f"<select name={name!r}> on SvestenikForm must be select2",
            )


class DomacinstvoFormFkSelect2Tests(_LoggedInAdminMixin, TestCase):
    """Every FK on DomacinstvoForm renders as <select class="django-select2">."""

    FK_FIELDS = ("domacin", "adresa", "slava")

    def test_every_fk_select_carries_django_select2_class(self):
        r = self.client.get(reverse("unos_domacinstva"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for name in self.FK_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=f"<select name={name!r}> on DomacinstvoForm must be select2",
            )


class IzmenaKrstenjeFkSelect2Tests(_LoggedInAdminMixin, TestCase):
    """The edit page preserves django-select2 init on every FK <select>."""

    FK_FIELDS = ("dete", "otac", "majka", "kum", "svestenik", "hram")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.krstenje = Krstenje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 2, 10),
            dete_rodjeno_zivo=True,
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )

    def test_edit_page_keeps_select2_on_every_fk(self):
        r = self.client.get(
            reverse("izmena_krstenja", kwargs={"uid": self.krstenje.uid})
        )
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for name in self.FK_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=f"<select name={name!r}> on edit page must be select2",
            )


class IzmenaVencanjaFkSelect2Tests(_LoggedInAdminMixin, TestCase):
    """The edit page preserves django-select2 init on every FK <select>."""

    FK_FIELDS = (
        "zenik",
        "nevesta",
        "kum",
        "svekar",
        "svekrva",
        "tast",
        "tasta",
        "stari_svat",
        "svestenik",
        "hram",
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 1),
        )

    def test_edit_page_keeps_select2_on_every_fk(self):
        r = self.client.get(
            reverse("izmena_vencanja", kwargs={"uid": self.vencanje.uid})
        )
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for name in self.FK_FIELDS:
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*class="[^"]*django-select2[^"]*"',
                msg=f"<select name={name!r}> on edit page must be select2",
            )


class SvestenikAdresaFkTests(TestCase):
    """Category B: Svestenik.adresa FK was added and roundtrips through the ORM."""

    def test_svestenik_can_have_adresa_fk(self):
        from registar.models import Adresa, Svestenik

        adresa = Adresa.objects.create(
            ulica="Господар Јованова",
            broj="12",
            mesto="Београд",
        )
        s = Svestenik.objects.create(
            ime="Тест",
            prezime="Свештеник",
            zvanje="Јереј",
            adresa=adresa,
        )
        fetched = Svestenik.objects.get(pk=s.pk)
        self.assertEqual(fetched.adresa_id, adresa.uid)
        self.assertEqual(fetched.adresa.mesto, "Београд")

    def test_svestenik_adresa_is_nullable(self):
        from registar.models import Svestenik

        s = Svestenik.objects.create(
            ime="Без",
            prezime="Адресе",
            zvanje="Јереј",
        )
        self.assertIsNone(s.adresa)

    def test_svestenik_form_adresa_widget_is_select2(self):
        from registar.forms import SvestenikForm
        from registar.forms.select2 import ScriptAwareModelSelect2Widget

        form = SvestenikForm()
        widget = form.fields["adresa"].widget
        self.assertIsInstance(widget, ScriptAwareModelSelect2Widget)
        rendered = str(form["adresa"])
        self.assertIn('class="django-select2', rendered)

    def test_unos_svestenika_renders_adresa_field(self):
        admin = User.objects.create_superuser(
            username="adresa-tester", email="a@x.test", password="x"
        )
        client = Client()
        client.force_login(admin)
        r = client.get(reverse("unos_svestenika"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertRegex(
            html,
            r'<select[^>]*name="adresa"[^>]*class="[^"]*django-select2[^"]*"',
        )
