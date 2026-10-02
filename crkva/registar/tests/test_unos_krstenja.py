"""Mock сејање крштења (registar.uvoz.seed.unos_krstenja)."""

import datetime
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from registar.mock import generators as g
from registar.models import Krstenje, Osoba, Svestenik
from registar.uvoz.seed.unos_krstenja import Command as UnosKrstenja


def _osoba(ime, pol, godine):
    """Особа задатог пола, стара отприлике `godine` година."""
    return Osoba.objects.create(
        ime=ime,
        prezime="Тест",
        pol=pol,
        datum_rodjenja=g.TODAY - datetime.timedelta(days=365 * godine + 30),
    )


class UnosKrstenjaTests(TestCase):
    """Улоге, грешке, --reset и понављање са --seed."""

    def _sej(self, *args):
        """Покреће команду над тест тенантом; враћа излаз."""
        out = StringIO()
        call_command(UnosKrstenja(), "--tenant", "test_tenant", *args, stdout=out)
        return out.getvalue()

    def _odrasli(self):
        """По двоје одраслих оба пола и један свештеник."""
        _osoba("Марко", "М", 40)
        _osoba("Петар", "М", 35)
        _osoba("Ана", "Ж", 38)
        _osoba("Јана", "Ж", 33)
        Svestenik.objects.create(ime="Сава", prezime="Савић", zvanje="јереј")

    def test_only_mock_source(self):
        """Други извор осим mock се одбија."""
        with self.assertRaisesMessage(CommandError, "само --from mock"):
            self._sej("--from", "dbf")

    def test_requires_children(self):
        """Без деце млађе од пет година нема сејања."""
        self._odrasli()
        with self.assertRaisesMessage(CommandError, "Нема деце"):
            self._sej()

    def test_requires_adults_of_both_sexes(self):
        """Без одраслих оба пола нема родитеља."""
        _osoba("Мали", "М", 1)
        _osoba("Марко", "М", 40)
        with self.assertRaisesMessage(CommandError, "одраслих оба пола"):
            self._sej()

    def test_one_baptism_per_child_with_valid_roles(self):
        """Свако дете добија једно крштење; отац мушкарац, мајка жена."""
        self._odrasli()
        deca = [_osoba(f"Дете{i}", "М", 1) for i in range(3)]
        out = self._sej("--seed", "1", "--count", "10")
        self.assertIn("Креирано 3 крштења", out)
        krstenja = Krstenje.objects.order_by("redni_broj")
        self.assertEqual([k.redni_broj for k in krstenja], [1, 2, 3])
        self.assertEqual({k.dete_id for k in krstenja}, {d.uid for d in deca})
        for k in krstenja:
            self.assertEqual((k.otac.pol, k.majka.pol), ("М", "Ж"))
            self.assertNotEqual(k.kum_id, k.dete_id)
            self.assertLessEqual(k.dete.datum_rodjenja, k.datum)
            self.assertTrue(1 <= (k.datum_registracije - k.datum).days <= 7)
            self.assertIsNotNone(k.svestenik)

    def test_count_limits_children(self):
        """--count ограничава број крштења."""
        self._odrasli()
        for i in range(3):
            _osoba(f"Дете{i}", "Ж", 2)
        self._sej("--count", "2")
        self.assertEqual(Krstenje.objects.count(), 2)

    def test_reset_deletes_previous(self):
        """--reset брише постојећа крштења пре сејања."""
        self._odrasli()
        _osoba("Дете", "М", 1)
        self._sej("--seed", "1")
        out = self._sej("--seed", "1", "--reset")
        self.assertIn("Обрисано 1 крштења.", out)
        self.assertEqual(Krstenje.objects.count(), 1)

    def test_same_seed_same_data(self):
        """Исти --seed даје исте улоге и датуме."""
        self._odrasli()
        _osoba("Дете", "М", 1)

        def snimak():
            k = Krstenje.objects.get()
            return (k.otac.ime, k.majka.ime, k.kum.ime, k.datum, k.mesto_registracije)

        self._sej("--seed", "42")
        prvi = snimak()
        self._sej("--seed", "42", "--reset")
        self.assertEqual(snimak(), prvi)
