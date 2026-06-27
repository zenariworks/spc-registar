"""Custom test runner that sets up a tenant schema for tests.

With django-tenants every ORM call must go through a tenant-aware
connection state. Plain `TestCase` opens a fresh transaction for each
test which can reset the connection\s tenant, so we:

  1) Migrate (which builds public + the migration-created tenant schemas).
  2) Create / promote a dedicated `test_tenant` schema as the system
     default.
  3) Monkey-patch `SimpleTestCase._pre_setup` (a classmethod) so every
     test starts with the test tenant active on the connection.
"""

from __future__ import annotations

from django.db import connection
from django.test import SimpleTestCase
from django.test.runner import DiscoverRunner


class TenantTestRunner(DiscoverRunner):
    """DiscoverRunner that ensures the test tenant is active per-test."""

    TEST_TENANT_SCHEMA = "test_tenant"
    TEST_TENANT_NAZIV = "Test Tenant"

    def setup_databases(self, **kwargs):
        old_config = super().setup_databases(**kwargs)
        tenant = self._create_test_tenant()
        self._install_pre_setup_hook(tenant)
        return old_config

    @classmethod
    def _create_test_tenant(cls):
        from tenants.models import Tenant

        # The unique constraint allows only one is_default=True row, so
        # clear any existing default first (the data migration may have
        # set one).
        Tenant.objects.filter(is_default=True).update(is_default=False)

        if Tenant.objects.filter(schema_name=cls.TEST_TENANT_SCHEMA).exists():
            tenant = Tenant.objects.get(schema_name=cls.TEST_TENANT_SCHEMA)
            tenant.is_default = True
            tenant.is_active = True
            tenant.save(update_fields=["is_default", "is_active"])
        else:
            tenant = Tenant(
                schema_name=cls.TEST_TENANT_SCHEMA,
                naziv=cls.TEST_TENANT_NAZIV,
                is_active=True,
                is_default=True,
            )
            tenant.save()  # auto_create_schema=True → schema + migrations
        connection.set_tenant(tenant)
        return tenant

    @staticmethod
    def _install_pre_setup_hook(tenant) -> None:
        """Ensure every test case runs with the test tenant on the connection."""
        # _pre_setup is a classmethod in Django; the underlying function
        # accepts the instance as its first positional arg when bound.
        original_func = SimpleTestCase.__dict__["_pre_setup"].__func__

        def _patched(self):  # noqa: ANN001
            connection.set_tenant(tenant)
            return original_func(self)

        SimpleTestCase._pre_setup = classmethod(_patched)

        # _pre_setup only fires per test instance. setUpTestData runs once in
        # setUpClass, BEFORE the first _pre_setup -- so if an earlier test class
        # left the connection on another schema (e.g. test_switch calls
        # connection.set_tenant() directly), this class would build its data in
        # the wrong schema and request-driven assertions would 404. Guard
        # setUpClass too so setUpTestData always runs on the test tenant.
        original_setupclass = SimpleTestCase.__dict__["setUpClass"].__func__

        def _patched_setupclass(cls):  # noqa: ANN001
            connection.set_tenant(tenant)
            return original_setupclass(cls)

        SimpleTestCase.setUpClass = classmethod(_patched_setupclass)
