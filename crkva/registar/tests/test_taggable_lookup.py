"""Tests for the taggable lookup pattern."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from registar.forms.lookup import PendingLookup, TaggableLookupField
from registar.models import Narodnost, Osoba, Veroispovest, Zanimanje
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class TaggableLookupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.user = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.user, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.existing_zanimanje = Zanimanje.objects.create(naziv="Учитељ")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_select_existing_lookup_by_pk(self):
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Тест",
                "prezime": "Иван",
                "pol": "М",
                "zanimanje": str(self.existing_zanimanje.pk),
            },
        )
        self.assertEqual(r.status_code, 302)
        p = Osoba.objects.get(ime="Тест", prezime="Иван")
        self.assertEqual(p.zanimanje, self.existing_zanimanje)

    def test_create_new_lookup_from_typed_string(self):
        before = Zanimanje.objects.count()
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Нови",
                "prezime": "Иван",
                "pol": "М",
                "zanimanje": "Програмер",
                "veroispovest": "Православна",
                "narodnost": "Српска",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Zanimanje.objects.count(), before + 1)
        new = Zanimanje.objects.get(naziv="Програмер")
        p = Osoba.objects.get(ime="Нови", prezime="Иван")
        self.assertEqual(p.zanimanje, new)
        self.assertEqual(p.veroispovest.naziv, "Православна")
        self.assertEqual(p.narodnost.naziv, "Српска")

    def test_typed_string_matches_existing_creates_no_duplicate(self):
        before = Zanimanje.objects.count()
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Дупликат",
                "prezime": "Тест",
                "pol": "М",
                "zanimanje": "Учитељ",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Zanimanje.objects.count(), before)
        p = Osoba.objects.get(ime="Дупликат")
        self.assertEqual(p.zanimanje, self.existing_zanimanje)

    def test_invalid_form_does_not_create_lookup_orphan(self):
        # #252: ако друго поље падне на валидацији, нова lookup вредност
        # се НЕ сме уписати (раније ју је to_python правио прерано).
        before = Zanimanje.objects.count()
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Сироче",
                "prezime": "Тест",
                "pol": "М",
                "datum_rodjenja": "није-датум",
                "zanimanje": "ОрфанЗанимање",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Zanimanje.objects.count(), before)
        self.assertFalse(
            Zanimanje.objects.filter(naziv__iexact="ОрфанЗанимање").exists()
        )
        self.assertFalse(Osoba.objects.filter(ime="Сироче").exists())

    def test_typed_string_case_insensitive_reuse(self):
        # „учитељ“ (мала слова) се мапира на постојеће „Учитељ“ — без дупликата.
        before = Zanimanje.objects.count()
        r = self.client.post(
            reverse("unos_parohijana"),
            {"ime": "Мала", "prezime": "Слова", "pol": "Ж", "zanimanje": "учитељ"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Zanimanje.objects.count(), before)
        self.assertEqual(
            Osoba.objects.get(ime="Мала").zanimanje, self.existing_zanimanje
        )

    def test_typed_string_whitespace_normalized(self):
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Размак",
                "prezime": "Тест",
                "pol": "М",
                "zanimanje": "  Нови   Посао  ",
            },
        )
        self.assertEqual(r.status_code, 302)
        z = Zanimanje.objects.get(naziv="Нови Посао")
        self.assertEqual(Osoba.objects.get(ime="Размак").zanimanje, z)


class LookupModelConstraintTests(TestCase):
    def test_save_normalizes_naziv(self):
        z = Zanimanje.objects.create(naziv="  Лекар  ")
        z.refresh_from_db()
        self.assertEqual(z.naziv, "Лекар")

    def test_case_insensitive_unique_blocks_duplicate(self):
        Veroispovest.objects.create(naziv="Православна")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Veroispovest.objects.create(naziv="православна")

    def test_whitespace_variant_blocked_after_normalization(self):
        Narodnost.objects.create(naziv="Српска")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Narodnost.objects.create(naziv="  српска ")


class TaggableLookupFieldUnitTests(TestCase):
    def setUp(self):
        self.field = TaggableLookupField(
            queryset=Zanimanje.objects.all(), required=False
        )

    def test_empty_returns_none(self):
        self.assertIsNone(self.field.to_python(""))

    def test_pk_returns_instance(self):
        z = Zanimanje.objects.create(naziv="Пилот")
        self.assertEqual(self.field.to_python(str(z.pk)), z)

    def test_new_value_returns_pending_without_creating(self):
        before = Zanimanje.objects.count()
        result = self.field.to_python("НовоЗанимање")
        self.assertIsInstance(result, PendingLookup)
        self.assertEqual(result.label, "НовоЗанимање")
        self.assertEqual(Zanimanje.objects.count(), before)
