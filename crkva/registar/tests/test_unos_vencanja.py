"""Сејање венчања (unos_vencanja): парови, кум, --reset и грешке."""

import datetime
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from registar.models import Osoba, Svestenik, Vencanje
from registar.uvoz.seed.unos_vencanja import Command as UnosVencanja


def _osobe(pol, *godine):
    """Особе датог пола рођене датих година."""
    for i, godina in enumerate(godine):
        Osoba.objects.create(
            ime=f"{pol}{i}",
            prezime="Тест",
            pol=pol,
            datum_rodjenja=datetime.date(godina, 3, 4),
        )


class UnosVencanjaTests(TestCase):
    """Команда над тест шемом."""

    def _seed(self, *args):
        """Покреће команду и враћа њен излаз."""
        out = StringIO()
        call_command(
            UnosVencanja(), "--tenant", "test_tenant", "--seed", "1", *args, stdout=out
        )
        return out.getvalue()

    def test_creates_valid_marriages(self):
        """Женик је мушкарац, невеста жена, кум није супружник; нико није у два пара."""
        _osobe("М", 1970, 1975, 1980, 1985)
        _osobe("Ж", 1972, 1977, 1982)
        Svestenik.objects.create(ime="Петар", prezime="Поп", zvanje="јереј")
        out = self._seed("--count", "2")
        self.assertIn("Креирано 2 венчања", out)
        supruznici = []
        for v in Vencanje.objects.all():
            self.assertEqual((v.zenik.pol, v.nevesta.pol), ("М", "Ж"))
            self.assertNotIn(v.kum, (v.zenik, v.nevesta))
            self.assertIsNotNone(v.svestenik)
            supruznici += [v.zenik_id, v.nevesta_id]
        self.assertEqual(len(supruznici), len(set(supruznici)))

    def test_reset_deletes_existing(self):
        """--reset брише постојећа венчања пре сејања."""
        _osobe("М", 1970, 1975, 1980)
        _osobe("Ж", 1972, 1977)
        self._seed("--count", "1")
        out = self._seed("--count", "1", "--reset")
        self.assertIn("Обрисано 1 венчања.", out)
        self.assertEqual(Vencanje.objects.count(), 1)

    def test_without_kum_candidate_nothing_is_created(self):
        """Са једним мушкарцем нема кума, па нема ни венчања."""
        _osobe("М", 1980)
        _osobe("Ж", 1982)
        self.assertIn("Креирано 0 венчања", self._seed())

    def test_errors(self):
        """Други извор, мањак одраслих и превелика разлика у годинама."""
        with self.assertRaisesMessage(CommandError, "само --from mock"):
            self._seed("--from", "dbf")
        _osobe("М", 1940)
        with self.assertRaisesMessage(CommandError, "Нема довољно одраслих"):
            self._seed()
        _osobe("Ж", 1995)
        with self.assertRaisesMessage(CommandError, "Нема компатибилних парова"):
            self._seed()
