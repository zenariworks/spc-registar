"""Канаринац: ``TenantTestRunner`` држи тест-тенант активним (#304).

``TenantTestRunner`` monkey-patch-ује ``SimpleTestCase._pre_setup`` и
``setUpClass`` да закуца ``test_tenant`` шему. То је део најизложенији
Django test интернал-има, па тврдимо да је конекција на тест-тенанту
током обичног ``TestCase`` — рано упозорење ако Django надоградња
промени те интерне делове.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.db import connection
from django.test import TestCase


class RunnerTenantActiveTests(TestCase):
    def test_connection_on_test_tenant(self):
        self.assertEqual(connection.schema_name, "test_tenant")
