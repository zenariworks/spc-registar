"""HandleMissingTablesMiddleware turns any missing-relation error into a 503 (#229).

Previously only four hardcoded table names were handled, so a fall-back to the
public schema that queried `domacinstva` or `slave` produced a raw 500.
"""

# pylint: disable=missing-function-docstring

from django.contrib.auth.models import AnonymousUser
from django.db import ProgrammingError
from django.test import RequestFactory, TestCase
from registar.middleware import HandleMissingTablesMiddleware
from tenants.models import Tenant


class MissingTablesMiddlewareTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")

    def setUp(self):
        self.mw = HandleMissingTablesMiddleware(lambda r: None)

    def _request(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        request.tenant = self.tenant
        return request

    def _missing(self, table):
        return ProgrammingError(
            f"relation \"{table}\" does not exist\nLINE 1: SELECT ..."
        )

    def test_domacinstva_missing_returns_503(self):
        resp = self.mw.process_exception(self._request(), self._missing("domacinstva"))
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 503)
        self.assertIn("домаћинства", resp.content.decode("utf-8"))

    def test_slave_missing_returns_503(self):
        resp = self.mw.process_exception(self._request(), self._missing("slave"))
        self.assertEqual(resp.status_code, 503)
        self.assertIn("славе", resp.content.decode("utf-8"))

    def test_known_registar_table_still_handled(self):
        resp = self.mw.process_exception(self._request(), self._missing("krstenja"))
        self.assertEqual(resp.status_code, 503)
        self.assertIn("крштења", resp.content.decode("utf-8"))

    def test_unknown_table_falls_back_to_raw_name(self):
        resp = self.mw.process_exception(self._request(), self._missing("neka_tabela"))
        self.assertEqual(resp.status_code, 503)
        self.assertIn("neka_tabela", resp.content.decode("utf-8"))

    def test_non_missing_relation_programming_error_passes_through(self):
        exc = ProgrammingError("syntax error at or near SELECT")
        self.assertIsNone(self.mw.process_exception(self._request(), exc))

    def test_non_programming_error_passes_through(self):
        self.assertIsNone(
            self.mw.process_exception(self._request(), ValueError("boom"))
        )
