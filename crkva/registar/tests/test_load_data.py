"""load_data --from mock: избор корака, провере и аргументи сваког корака."""

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from registar.management.commands import load_data


class LoadDataMockTests(SimpleTestCase):
    """Сејање по корацима, без стварног позива seedera."""

    def pokreni(self, *args):
        """Позиви корака као (назив, kwargs) и излаз команде."""
        out = StringIO()
        with mock.patch.object(load_data, "call_command") as poziv:
            call_command("load_data", "--from", "mock", *args, stdout=out)
        pozivi = [
            (c.args[0].__module__.rsplit(".", 1)[-1], c.kwargs)
            for c in poziv.call_args_list
        ]
        return pozivi, out.getvalue()

    def test_default_counts_and_flags(self):
        """Без --count сваки корак добија свој подразумевани број."""
        pozivi, out = self.pokreni("--tenant", "t")
        self.assertEqual(
            pozivi,
            [
                ("unos_sifarnika", {"tenant": "t"}),
                ("unos_adresa", {"source": "mock", "tenant": "t", "count": 30}),
                ("unos_svestenika", {"source": "mock", "tenant": "t", "count": 5}),
                ("unos_parohijana", {"source": "mock", "tenant": "t", "count": 100}),
                ("unos_domacinstava", {"source": "mock", "tenant": "t", "count": 33}),
                ("unos_krstenja", {"source": "mock", "tenant": "t", "count": 25}),
                ("unos_vencanja", {"source": "mock", "tenant": "t", "count": 10}),
            ],
        )
        self.assertIn("(7 корака, tenant=t, reset=False)", out)
        self.assertIn("load_data завршен.", out)

    def test_count_seed_and_reset_are_passed(self):
        """--count се скалира делиоцем (најмање 1), seed и reset се прослеђују."""
        pozivi, _ = self.pokreni(
            "--tenant",
            "t",
            "--count",
            "30",
            "--seed",
            "7",
            "--reset",
            "--only",
            "unos_sifarnika,unos_svestenika,unos_adresa",
        )
        self.assertEqual(
            pozivi,
            [
                ("unos_sifarnika", {"tenant": "t"}),
                (
                    "unos_adresa",
                    {
                        "source": "mock",
                        "tenant": "t",
                        "count": 10,
                        "seed": 7,
                        "reset": True,
                    },
                ),
                (
                    "unos_svestenika",
                    {
                        "source": "mock",
                        "tenant": "t",
                        "count": 1,
                        "seed": 7,
                        "reset": True,
                    },
                ),
            ],
        )

    def test_dry_run_calls_nothing(self):
        """--dry-run наводи кораке без позива."""
        pozivi, out = self.pokreni(
            "--tenant", "t", "--dry-run", "--only", "unos_adresa"
        )
        self.assertEqual(pozivi, [])
        self.assertIn("→ Адресе  (manage.py unos_adresa)", out)
        self.assertIn("(dry-run — прескачем)", out)
        self.assertIn("Dry-run завршен.", out)

    def test_unknown_only_is_rejected(self):
        """--only без иједног познатог корака је грешка са списком."""
        with self.assertRaisesMessage(
            CommandError, "Доступни: unos_sifarnika, unos_adresa"
        ):
            self.pokreni("--tenant", "t", "--only", "nema")

    def test_tenant_is_required(self):
        """Без --tenant per-tenant кораци се одбијају."""
        with self.assertRaisesMessage(CommandError, "--tenant је обавезан"):
            self.pokreni("--only", "unos_adresa")
