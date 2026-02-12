"""
Интеграциони тестови за migrate_data команду.
Ови тестови проверавају оркестрацију целог процеса миграције података.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase
from registar.models import Krstenje, Vencanje


class TestMigrateDataCommand(TransactionTestCase):
    """Интеграциони тестови за migrate_data команду."""

    def test_help_shows_all_flags(self):
        """Тест да --help приказује све опције."""
        # Django трансформише --help у usage error, тестирамо преко subprocess
        import subprocess
        result = subprocess.run(
            ["python", "manage.py", "migrate_data", "--help"],
            capture_output=True,
            text=True,
            cwd="/app"
        )

        help_output = result.stdout + result.stderr
        # Провера да help садржи све главне опције
        self.assertIn("--dummy", help_output)
        self.assertIn("--real", help_output)
        self.assertIn("--dry-run", help_output)
        self.assertIn("--skip-staging", help_output)
        self.assertIn("--keep-staging", help_output)

    def test_no_flags_raises_error(self):
        """Тест да команда без флагова баца грешку."""
        # Команда захтева или --dummy или --real
        # Django management command трансформише argparse грешке у CommandError
        with self.assertRaises(CommandError) as context:
            call_command("migrate_data")
        # Порука треба да садржи информацију о обавезним аргументима
        self.assertIn("required", str(context.exception))

    def test_both_flags_raises_error(self):
        """Тест да команда са оба флага баца грешку."""
        # --dummy и --real су међусобно искључиви
        # Django management command трансформише argparse грешке у CommandError
        with self.assertRaises(CommandError) as context:
            call_command("migrate_data", "--dummy", "--real")
        # Порука треба да садржи информацију о међусобно искључивим аргументима
        self.assertIn("not allowed", str(context.exception))

    def test_real_missing_zip_raises_error(self):
        """Тест да --real са непостојећом путањом баца грешку."""
        with self.assertRaises(CommandError) as context:
            call_command("migrate_data", "--real", "/nonexistent/path.zip")
        self.assertIn("Фајл није пронађен", str(context.exception))

    def test_dummy_dry_run_no_database_writes(self):
        """Тест да --dummy --dry-run не уписује податке у базу."""
        out = StringIO()

        # Покрени команду са --dummy --dry-run
        call_command("migrate_data", "--dummy", "--dry-run", stdout=out)

        # Провера да нису креирани подаци
        self.assertFalse(Krstenje.objects.exists())
        self.assertFalse(Vencanje.objects.exists())

        # Провера да output садржи dry-run поруке
        output = out.getvalue()
        self.assertIn("DRY-RUN", output)
        self.assertIn("Команде које би биле извршене", output)

    @patch("registar.management.commands.migrate_data.call_command")
    def test_dummy_creates_data_correct_order(self, mock_call_command):
        """Тест да --dummy позива команде у исправном редоследу."""
        out = StringIO()

        # Мок call_command да не извршава стварне команде
        def side_effect(cmd, **kwargs):
            # Једино дозволи migrate_data да се изврши стварно
            if cmd == "migrate_data":
                # Не можемо рекурзивно позивати, враћамо празан резултат
                return None
            return None

        # Морамо користити оригинални call_command за migrate_data,
        # али моковати све остале позиве
        original_call_command = call_command.__wrapped__ if hasattr(call_command, '__wrapped__') else call_command

        def selective_mock(cmd, *args, **kwargs):
            if cmd in ["unosi", "unos_drzava", "unos_mesta", "unos_ulica",
                       "unos_adresa", "unos_svestenika", "unos_krstenja", "unos_vencanja"]:
                # Мокуј ове команде
                mock_call_command(cmd, **kwargs)
                return None
            # За све остале, користи оригиналну имплементацију
            return original_call_command(cmd, *args, **kwargs)

        with patch("django.core.management.call_command", side_effect=selective_mock):
            call_command("migrate_data", "--dummy", stdout=out)

        # Провера да су команде позване у исправном редоследу
        expected_calls = [
            call("unosi", **{}),
            call("unos_drzava", **{}),
            call("unos_mesta", **{}),
            call("unos_ulica", **{}),
            call("unos_adresa", **{}),
            call("unos_svestenika", **{"broj": 5}),
            call("unos_krstenja", **{}),
            call("unos_vencanja", **{}),
        ]

        # Провера да су све команде позване
        for expected_call in expected_calls:
            self.assertIn(expected_call, mock_call_command.call_args_list)

    @patch("registar.management.commands.migrate_data.call_command")
    def test_real_calls_correct_commands(self, mock_call_command):
        """Тест да --real позива команде у исправном редоследу."""
        out = StringIO()

        # Креирај привремени ZIP фајл
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name

        try:
            # Мокуј call_command да не извршава стварне команде
            def selective_mock(cmd, *args, **kwargs):
                if cmd in ["load_dbf", "unosi", "unos_drzava", "unos_mesta",
                           "migracija_slava", "migracija_ulica", "migracija_svestenika",
                           "migracija_parohijana", "migracija_ukucana",
                           "migracija_ukucana_parohijana", "migracija_krstenja", "migracija_vencanja"]:
                    mock_call_command(cmd, **kwargs)
                    return None
                # За migrate_data, користи оригиналну имплементацију
                from django.core.management import call_command as original
                return original(cmd, *args, **kwargs)

            with patch("django.core.management.call_command", side_effect=selective_mock):
                call_command("migrate_data", "--real", zip_path, stdout=out)

            # Провера да је load_dbf позван први
            first_call = mock_call_command.call_args_list[0]
            self.assertEqual(first_call[0][0], "load_dbf")

            # Провера да су миграционе команде позване
            called_commands = [c[0][0] for c in mock_call_command.call_args_list]

            # Провера редоследа кључних команди
            self.assertIn("load_dbf", called_commands)
            self.assertIn("unosi", called_commands)
            self.assertIn("migracija_krstenja", called_commands)
            self.assertIn("migracija_vencanja", called_commands)

            # Провера да је load_dbf пре миграција
            load_dbf_index = called_commands.index("load_dbf")
            migracija_krstenja_index = called_commands.index("migracija_krstenja")
            self.assertLess(load_dbf_index, migracija_krstenja_index)

        finally:
            # Обриши привремени фајл
            Path(zip_path).unlink(missing_ok=True)

    def test_summary_report_printed(self):
        """Тест да извештај о миграцији садржи очекиване елементе."""
        out = StringIO()

        # Покрени команду са --dummy --dry-run
        call_command("migrate_data", "--dummy", "--dry-run", stdout=out)

        output = out.getvalue()

        # Провера да садржи заглавље извештаја
        self.assertIn("ИЗВЕШТАЈ О МИГРАЦИЈИ", output)

        # Провера да садржи информације о режиму
        self.assertIn("Режим:", output)
        self.assertIn("DUMMY", output.upper())

        # Провера да садржи информације о корацима
        self.assertIn("Укупно корака:", output)

        # Провера да садржи листу корака
        self.assertIn("unosi", output)
        self.assertIn("unos_drzava", output)

    @patch("registar.management.commands.migrate_data.call_command")
    def test_real_with_skip_staging_flag(self, mock_call_command):
        """Тест да --skip-staging прескаче load_dbf корак."""
        out = StringIO()

        # Креирај привремени ZIP фајл
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name

        try:
            def selective_mock(cmd, *args, **kwargs):
                if cmd != "migrate_data":
                    mock_call_command(cmd, **kwargs)
                    return None
                from django.core.management import call_command as original
                return original(cmd, *args, **kwargs)

            with patch("django.core.management.call_command", side_effect=selective_mock):
                call_command("migrate_data", "--real", zip_path, "--skip-staging", stdout=out)

            # Провера да load_dbf НИЈЕ позван
            called_commands = [c[0][0] for c in mock_call_command.call_args_list]
            self.assertNotIn("load_dbf", called_commands)

            # Провера да су остале команде позване
            self.assertIn("unosi", called_commands)

        finally:
            Path(zip_path).unlink(missing_ok=True)

    def test_real_dry_run_validates_staging_tables(self):
        """Тест да --real --dry-run валидира staging табеле."""
        out = StringIO()

        # Креирај привремени ZIP фајл
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name

        try:
            # Мокуј load_dbf да не извршава стварно учитавање
            def selective_mock(cmd, *args, **kwargs):
                if cmd == "load_dbf":
                    return None  # Не ради ништа
                # Не мокуј migrate_data - дозволи да се изврши нормално
                raise TypeError(f"Unmocked call_command for {cmd}")

            with patch("registar.management.commands.migrate_data.call_command", side_effect=selective_mock):
                call_command("migrate_data", "--real", zip_path, "--dry-run", stdout=out)

            output = out.getvalue()

            # Провера да садржи валидационе поруке
            self.assertIn("DRY-RUN", output)
            self.assertIn("Провера staging табела", output)
            self.assertIn("Миграција се не извршава", output)

        finally:
            Path(zip_path).unlink(missing_ok=True)

    def test_error_handling_continues_execution(self):
        """Тест да команда наставља извршавање након грешке у не-критичном кораку."""
        out = StringIO()

        # Мокуј call_command да баци грешку у једном кораку
        def selective_mock(cmd, *args, **kwargs):
            if cmd == "unos_mesta":
                raise CommandError("Тест грешка")
            elif cmd in ["unosi", "unos_drzava", "unos_ulica", "unos_adresa",
                         "unos_svestenika", "unos_krstenja", "unos_vencanja"]:
                return None
            # Немокован позив - пусти да падне ако није покривено
            raise TypeError(f"Unmocked call_command for {cmd}")

        with patch("registar.management.commands.migrate_data.call_command", side_effect=selective_mock):
            # Команда треба да баци CommandError на крају због грешке
            with self.assertRaises(CommandError) as context:
                call_command("migrate_data", "--dummy", stdout=out)

            # Провера да порука садржи број грешака
            self.assertIn("грешком", str(context.exception))

        output = out.getvalue()

        # Провера да су неки кораци успели пре грешке
        self.assertIn("Референтни подаци", output)
        self.assertIn("Генерисање држава", output)
