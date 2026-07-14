"""#330: увоз/чишћење не сме да дира ДРУГЕ закупце ни public.

``popravi_*`` су подразумевано петљали кроз СВЕ закупце када ``--schema``
није дат, па је увоз једне парохије брисао/преписивао податке других.
``importuj_dbf`` (и ``migracija_*``) су се смели покренути над public шемом.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase
from django_tenants.utils import schema_context
from registar.management.commands._schema_target import razresi_ciljne_sheme
from registar.uvoz.krstenja import Command as MigracijaKrstenja
from tenants.models import Zakupac


class ResolveTargetSchemasTests(TestCase):
    def test_default_is_active_schema_only(self):
        # Test runner keeps `test_tenant` active on the connection.
        self.assertEqual(connection.schema_name, "test_tenant")
        self.assertEqual(razresi_ciljne_sheme({}), ["test_tenant"])

    def test_default_refuses_public(self):
        with schema_context("public"):
            with self.assertRaises(CommandError):
                razresi_ciljne_sheme({})

    def test_explicit_schema_returns_that_one(self):
        self.assertEqual(
            razresi_ciljne_sheme({"schema": "test_tenant"}), ["test_tenant"]
        )

    def test_unknown_schema_raises(self):
        with self.assertRaises(CommandError):
            razresi_ciljne_sheme({"schema": "nema_ovakve_sheme"})

    def test_all_tenants_lists_non_public(self):
        result = razresi_ciljne_sheme({"all_tenants": True})
        self.assertIn("test_tenant", result)
        self.assertNotIn("public", result)

    def test_all_tenants_and_schema_conflict(self):
        with self.assertRaises(CommandError):
            razresi_ciljne_sheme({"all_tenants": True, "schema": "test_tenant"})


class PopraviDefaultDoesNotTouchOtherTenantsTests(TestCase):
    def test_no_schema_flag_processes_only_active_schema(self):
        # A second tenant row exists but must NOT be visited by the default run.
        # bulk_create skips schema provisioning; if the command looped all
        # tenants it would enter this (unprovisioned) schema and blow up.
        Zakupac.objects.bulk_create(
            [Zakupac(schema_name="test_tenant_other", naziv="Other", is_active=True)]
        )
        out = StringIO()
        # Must not raise and must only mention the active schema.
        call_command("popravi_duplikate", "--dry-run", stdout=out)
        printed = out.getvalue()
        self.assertIn("test_tenant", printed)
        self.assertNotIn("test_tenant_other", printed)

    def test_all_tenants_flag_opts_into_the_loop(self):
        out = StringIO()
        call_command("popravi_devojacka", "--dry-run", "--all-tenants", stdout=out)
        self.assertIn("test_tenant", out.getvalue())


class ImportujDbfPublicGuardTests(TestCase):
    def test_refuses_public_schema(self):
        with schema_context("public"):
            with self.assertRaises(CommandError):
                call_command("importuj_dbf", "--dry-run")

    def test_runs_dry_under_active_tenant(self):
        # Active schema is test_tenant → guard passes, dry-run prints the plan.
        out = StringIO()
        call_command("importuj_dbf", "--dry-run", stdout=out)
        self.assertIn("dry", out.getvalue().lower())


class MigracijaPublicGuardTests(TestCase):
    def test_migracija_krstenja_refuses_public(self):
        with schema_context("public"):
            with self.assertRaises(CommandError):
                call_command(MigracijaKrstenja(), "--dry-run")
