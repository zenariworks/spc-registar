"""Smoke тестови за ``wait_for_db`` команду (#304).

``wait_for_db`` је гејт за покретање контејнера: блокира док база не
одговори, па се враћа. Оба тока проверавамо без стварне базе — ``check``
се патцхује да прво падне неколико пута па успе, а ``time.sleep`` да
петља не чека заиста.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase

CHECK = "registar.management.commands.wait_for_db.Command.check"
SLEEP = "registar.management.commands.wait_for_db.time.sleep"


class WaitForDbCommandTests(SimpleTestCase):
    def test_returns_when_db_up(self):
        with patch(CHECK) as mocked_check:
            call_command("wait_for_db", stdout=StringIO())
        mocked_check.assert_called_once_with(databases=["default"])

    def test_retries_until_db_available(self):
        with patch(SLEEP) as mocked_sleep, patch(CHECK) as mocked_check:
            mocked_check.side_effect = [OperationalError] * 3 + [True]
            out = StringIO()
            call_command("wait_for_db", stdout=out)
        self.assertEqual(mocked_check.call_count, 4)
        self.assertEqual(mocked_sleep.call_count, 3)
        self.assertIn("доступна", out.getvalue())
