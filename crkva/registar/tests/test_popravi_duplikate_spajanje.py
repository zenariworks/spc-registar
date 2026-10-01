"""Карактеризациони тестови за `popravi_duplikate` (спајање особа).

Фиксирају понашање пре рефакторисања `_phase_osoba`/`_merge_osoba_into`:
по ком сигналу се особе истог имена спајају, која остаје канонска, како се
пребацују везе (домаћинство, укућани, крштења) и шта иде на људски преглед.
"""

# pylint: disable=missing-function-docstring

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from registar.models import Adresa, Domacinstvo, Krstenje, Osoba, Ukucanin


def _pokreni(*args):
    out = StringIO()
    call_command("popravi_duplikate", *args, stdout=out)
    return out.getvalue()


class SpajanjePoSignaluTests(TestCase):
    def test_isti_mobilni_spaja_u_bogatiju_osobu(self):
        siromasna = Osoba.objects.create(
            ime="Петар", prezime="Петровић", tel_mobilni="+381641234567"
        )
        bogata = Osoba.objects.create(
            ime="петар ",
            prezime="ПЕТРОВИЋ",
            tel_mobilni="+381641234567",
            pol="М",
            mesto_rodjenja="Београд",
        )

        izlaz = _pokreni()

        self.assertIn("спојено 1 дупл. особа", izlaz)
        self.assertFalse(Osoba.objects.filter(pk=siromasna.pk).exists())
        self.assertTrue(Osoba.objects.filter(pk=bogata.pk).exists())

    def test_ista_adresa_spaja_i_dopunjuje_polja(self):
        adresa = Adresa.objects.create(ulica="Света", broj="1", mesto="Београд")
        prva = Osoba.objects.create(
            ime="Ана", prezime="Анић", adresa=adresa, pol="Ж", parohijan=True
        )
        druga = Osoba.objects.create(
            ime="Ана", prezime="Анић", adresa=adresa, mesto_rodjenja="Нови Сад"
        )

        _pokreni()

        self.assertFalse(Osoba.objects.filter(pk=druga.pk).exists())
        prva.refresh_from_db()
        self.assertEqual(prva.mesto_rodjenja, "Нови Сад")
        self.assertTrue(prva.parohijan)

    def test_adresa_domacinstva_kao_signal(self):
        adresa = Adresa.objects.create(ulica="Кућна", broj="2", mesto="Београд")
        prva = Osoba.objects.create(ime="Јован", prezime="Јовић", pol="М")
        druga = Osoba.objects.create(ime="Јован", prezime="Јовић")
        Domacinstvo.objects.create(domacin=prva, adresa=adresa)
        Domacinstvo.objects.create(domacin=druga, adresa=adresa)

        _pokreni()

        self.assertEqual(Osoba.objects.filter(ime="Јован").count(), 1)
        self.assertEqual(Domacinstvo.objects.filter(adresa=adresa).count(), 1)

    def test_bez_signala_ide_na_pregled_i_ne_dira_se(self):
        Osoba.objects.create(ime="Мила", prezime="Милић")
        Osoba.objects.create(ime="Мила", prezime="Милић")

        izlaz = _pokreni()

        self.assertEqual(Osoba.objects.filter(ime="Мила").count(), 2)
        self.assertIn("спојено 0 дупл. особа", izlaz)
        self.assertIn("пријављено за људски преглед: 1 група", izlaz)

    def test_razliciti_signali_se_ne_spajaju(self):
        Osoba.objects.create(ime="Лука", prezime="Лукић", tel_mobilni="+381641111111")
        Osoba.objects.create(ime="Лука", prezime="Лукић", tel_mobilni="+381642222222")

        izlaz = _pokreni()

        self.assertEqual(Osoba.objects.filter(ime="Лука").count(), 2)
        self.assertIn("пријављено за људски преглед: 1 група", izlaz)

    def test_delimicno_poklapanje_spaja_podgrupu_a_ostatak_prijavljuje(self):
        Osoba.objects.create(ime="Ива", prezime="Ивић", tel_mobilni="+381643333333")
        Osoba.objects.create(ime="Ива", prezime="Ивић", tel_mobilni="+381643333333")
        Osoba.objects.create(ime="Ива", prezime="Ивић")

        izlaz = _pokreni()

        self.assertEqual(Osoba.objects.filter(ime="Ива").count(), 2)
        self.assertIn("спојено 1 дупл. особа", izlaz)
        self.assertIn("пријављено за људски преглед: 1 група", izlaz)

    def test_jedinstvene_osobe_se_ne_prijavljuju(self):
        Osoba.objects.create(ime="Сава", prezime="Савић", tel_mobilni="+381644444444")

        izlaz = _pokreni()

        self.assertIn("спојено 0 дупл. особа", izlaz)
        self.assertIn("пријављено за људски преглед: 0 група", izlaz)

    def test_dry_run_broji_a_ne_menja(self):
        Osoba.objects.create(ime="Нина", prezime="Нинић", tel_mobilni="+381645555555")
        Osoba.objects.create(ime="Нина", prezime="Нинић", tel_mobilni="+381645555555")

        izlaz = _pokreni("--dry-run")

        self.assertIn("би се спојено 1 дупл. особа", izlaz)
        self.assertEqual(Osoba.objects.filter(ime="Нина").count(), 2)


class PrebacivanjeVezaTests(TestCase):
    def setUp(self):
        self.kanonska = Osoba.objects.create(
            ime="Марко",
            prezime="Марковић",
            tel_mobilni="+381646666666",
            pol="М",
            parohijan=True,
        )
        self.dupla = Osoba.objects.create(
            ime="Марко", prezime="Марковић", tel_mobilni="+381646666666"
        )

    def test_krstenje_prelazi_na_kanonsku(self):
        krstenje = Krstenje.objects.create(
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            vanbracno=False,
            blizanac=False,
            telesna_mana=False,
            otac=self.dupla,
        )

        _pokreni()

        krstenje.refresh_from_db()
        self.assertEqual(krstenje.otac_id, self.kanonska.pk)

    def test_domacinstvo_duple_prelazi_na_kanonsku(self):
        dom = Domacinstvo.objects.create(domacin=self.dupla)

        _pokreni()

        dom.refresh_from_db()
        self.assertEqual(dom.domacin_id, self.kanonska.pk)

    def test_dva_domacinstva_se_spajaju_sa_ukucanima(self):
        clan = Osoba.objects.create(ime="Члан", prezime="Други")
        zajednicki = Osoba.objects.create(ime="Заједнички", prezime="Члан")
        dom_k = Domacinstvo.objects.create(domacin=self.kanonska)
        dom_d = Domacinstvo.objects.create(domacin=self.dupla, napomena="белешка")
        Ukucanin.objects.create(domacinstvo=dom_k, osoba=zajednicki)
        Ukucanin.objects.create(domacinstvo=dom_d, osoba=zajednicki)
        Ukucanin.objects.create(domacinstvo=dom_d, osoba=clan)

        _pokreni()

        self.assertFalse(Domacinstvo.objects.filter(pk=dom_d.pk).exists())
        dom_k.refresh_from_db()
        self.assertEqual(dom_k.napomena, "белешка")
        self.assertEqual(
            set(dom_k.ukucani.values_list("osoba_id", flat=True)),
            {zajednicki.pk, clan.pk},
        )

    def test_ukucanin_duple_prelazi_bez_dupliranja(self):
        dom = Domacinstvo.objects.create(
            domacin=Osoba.objects.create(ime="Глава", prezime="Куће")
        )
        drugi_dom = Domacinstvo.objects.create(
            domacin=Osoba.objects.create(ime="Друга", prezime="Глава")
        )
        Ukucanin.objects.create(domacinstvo=dom, osoba=self.kanonska)
        Ukucanin.objects.create(domacinstvo=dom, osoba=self.dupla)
        Ukucanin.objects.create(domacinstvo=drugi_dom, osoba=self.dupla)

        _pokreni()

        self.assertEqual(
            Ukucanin.objects.filter(domacinstvo=dom, osoba=self.kanonska).count(), 1
        )
        self.assertTrue(
            Ukucanin.objects.filter(domacinstvo=drugi_dom, osoba=self.kanonska).exists()
        )
        self.assertFalse(Ukucanin.objects.filter(osoba_id=self.dupla.pk).exists())
