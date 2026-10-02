"""Фабрике својстава која читају поља везане особе (registar.models._osoba_polja)."""

from types import SimpleNamespace

from django.test import SimpleTestCase
from registar.models._osoba_polja import (
    naziv_polja_osobe,
    polje_osobe,
    popunjeno_polje_osobe,
)


class Upis:
    """Упис са једном везаном особом."""

    ime = polje_osobe("osoba", "ime", opis="Име.")
    datum = polje_osobe("osoba", "datum", prazno=None)
    vera = popunjeno_polje_osobe("osoba", "vera")
    zanimanje = naziv_polja_osobe("osoba", "zanimanje")

    def __init__(self, osoba):
        self.osoba = osoba


class Zanimanje:
    """Шифарник са текстуалним приказом."""

    def __str__(self):
        return "учитељ"


class OsobaPoljaTests(SimpleTestCase):
    """Вредности са везаном особом и без ње."""

    def test_without_person_returns_empty_value(self):
        """Без особе: задата празна вредност, односно празан стринг."""
        upis = Upis(None)
        self.assertEqual(upis.ime, "")
        self.assertIsNone(upis.datum)
        self.assertEqual(upis.vera, "")
        self.assertEqual(upis.zanimanje, "")

    def test_with_person_returns_field_as_is(self):
        """polje_osobe враћа вредност поља непромењену, и кад је None."""
        self.assertEqual(Upis(SimpleNamespace(ime="Ана")).ime, "Ана")
        self.assertIsNone(Upis(SimpleNamespace(ime=None)).ime)

    def test_filled_field_or_empty_string(self):
        """popunjeno_polje_osobe враћа сам објекат или празан стринг."""
        vera = object()
        self.assertIs(Upis(SimpleNamespace(vera=vera)).vera, vera)
        self.assertEqual(Upis(SimpleNamespace(vera=None)).vera, "")

    def test_named_field_is_text(self):
        """naziv_polja_osobe враћа текстуални приказ поља."""
        self.assertEqual(
            Upis(SimpleNamespace(zanimanje=Zanimanje())).zanimanje, "учитељ"
        )
        self.assertEqual(Upis(SimpleNamespace(zanimanje=None)).zanimanje, "")

    def test_property_has_docstring(self):
        """Опис се преноси у docstring својства."""
        self.assertEqual(Upis.ime.__doc__, "Име.")
