"""Фабрике својстава која читају поља везане особе (registar.models._osoba_polja)."""

from types import SimpleNamespace

from django.test import SimpleTestCase
from registar.models._osoba_polja import (
    mala,
    naziv_polja_osobe,
    opis_osobe,
    opis_veze,
    polje_osobe,
    popunjeno_polje_osobe,
    spoji,
)


def napravi_upis():
    """Нова класа уписа са једном везаном особом.

    Класа се прави у самом тесту, а не при увозу модула, да би мутационо
    тестирање (mutmut) видело измене у фабрикама.
    """

    class Upis:
        ime = polje_osobe("osoba", "ime", opis="Име.")
        datum = polje_osobe("osoba", "datum", prazno=None)
        vera = popunjeno_polje_osobe("osoba", "vera")
        zanimanje = naziv_polja_osobe("osoba", "zanimanje")
        opis = opis_veze("osoba", opis="Опис особе.")

        def __init__(self, osoba):
            self.osoba = osoba

    return Upis


class Zanimanje:
    """Шифарник са текстуалним приказом."""

    def __str__(self):
        return "учитељ"


class OsobaPoljaTests(SimpleTestCase):
    """Вредности са везаном особом и без ње."""

    def test_without_person_returns_empty_value(self):
        """Без особе: задата празна вредност, односно празан стринг."""
        upis = napravi_upis()(None)
        self.assertEqual(upis.ime, "")
        self.assertIsNone(upis.datum)
        self.assertEqual(upis.vera, "")
        self.assertEqual(upis.zanimanje, "")

    def test_with_person_returns_field_as_is(self):
        """polje_osobe враћа вредност поља непромењену, и кад је None."""
        self.assertEqual(napravi_upis()(SimpleNamespace(ime="Ана")).ime, "Ана")
        self.assertIsNone(napravi_upis()(SimpleNamespace(ime=None)).ime)

    def test_filled_field_or_empty_string(self):
        """popunjeno_polje_osobe враћа сам објекат или празан стринг."""
        vera = object()
        self.assertIs(napravi_upis()(SimpleNamespace(vera=vera)).vera, vera)
        self.assertEqual(napravi_upis()(SimpleNamespace(vera=None)).vera, "")

    def test_named_field_is_text(self):
        """naziv_polja_osobe враћа текстуални приказ поља."""
        self.assertEqual(
            napravi_upis()(SimpleNamespace(zanimanje=Zanimanje())).zanimanje, "учитељ"
        )
        self.assertEqual(napravi_upis()(SimpleNamespace(zanimanje=None)).zanimanje, "")

    def test_property_has_docstring(self):
        """Опис се преноси у docstring својства."""
        self.assertEqual(napravi_upis().ime.__doc__, "Име.")

    def test_property_without_description_has_empty_docstring(self):
        """Без описа ниједна фабрика не даје docstring."""
        for svojstvo in (
            polje_osobe("osoba", "ime"),
            popunjeno_polje_osobe("osoba", "vera"),
            naziv_polja_osobe("osoba", "zanimanje"),
            opis_veze("osoba"),
        ):
            self.assertFalse(svojstvo.__doc__)


class OpisOsobeTests(SimpleTestCase):
    """Опис особе у једном реду."""

    def test_spoji_skips_empty_parts(self):
        """Празни делови и None се прескачу, делови се скраћују."""
        self.assertEqual(spoji(" Ана ", "", None, "  ", 5), "Ана, 5")
        self.assertEqual(spoji(), "")

    def test_mala_lowercases_text(self):
        """Мала слова за текстуални приказ; празна вредност даје празан стринг."""
        self.assertEqual(mala(Zanimanje()), "учитељ")
        self.assertEqual(mala("Српска"), "српска")
        self.assertEqual(mala(None), "")

    def test_opis_osobe_full(self):
        """Име презиме, занимање, место, па додатни делови малим словима."""
        adresa = SimpleNamespace(mesto="Чукарица")
        self.assertEqual(
            opis_osobe("Ана", "Петровић", Zanimanje(), adresa, "Православна", None),
            "Ана Петровић, учитељ, Чукарица, православна",
        )

    def test_opis_osobe_without_address_or_name_parts(self):
        """Без адресе и презимена нема празних делова ни зареза."""
        self.assertEqual(opis_osobe("Ана", None, "", None), "Ана")
        self.assertEqual(opis_osobe(None, None, None, None), "")

    def test_opis_veze(self):
        """opis_veze описује везану особу, без ње враћа празан стринг."""
        osoba = SimpleNamespace(
            ime="Марко",
            prezime="Илић",
            zanimanje=Zanimanje(),
            adresa=SimpleNamespace(mesto="Зандам"),
        )
        self.assertEqual(napravi_upis()(osoba).opis, "Марко Илић, учитељ, Зандам")
        self.assertEqual(napravi_upis()(None).opis, "")
        self.assertEqual(napravi_upis().opis.__doc__, "Опис особе.")
