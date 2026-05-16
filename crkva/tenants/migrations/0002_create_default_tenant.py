"""Create the default Tenant + provision its Postgres schema.

Uses the LIVE Tenant class (not the historical model) so we get
`auto_create_schema = True` behaviour — saving a Tenant triggers
schema creation and runs TENANT_APPS migrations against it.
"""

from django.conf import settings
from django.db import migrations


def create_default_tenant(apps, schema_editor):
    # Live model: we need its TenantMixin save() to auto-create the schema.
    from tenants.models import Tenant

    UserMembership = apps.get_model("tenants", "UserMembership")
    User = apps.get_model(
        settings.AUTH_USER_MODEL.split(".")[0],
        settings.AUTH_USER_MODEL.split(".")[1],
    )

    if Tenant.objects.filter(schema_name="crkva_sv_petke_cukarica").exists():
        tenant = Tenant.objects.get(schema_name="crkva_sv_petke_cukarica")
    else:
        # save() triggers create_schema() because auto_create_schema=True.
        tenant = Tenant(
            schema_name="crkva_sv_petke_cukarica",
            naziv="Парохија Чукарица",
            parohija_naziv="Парохија Чукарица",
            is_active=True,
            is_default=True,
        )
        tenant.save()

    if not tenant.is_default:
        Tenant.objects.exclude(pk=tenant.pk).update(is_default=False)
        tenant.is_default = True
        tenant.save()

    for user in User.objects.filter(is_active=True, is_staff=True):
        UserMembership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={"role": "admin", "is_default": True},
        )


def remove_default_tenant(apps, schema_editor):
    from tenants.models import Tenant

    Tenant.objects.filter(schema_name="crkva_sv_petke_cukarica").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_tenant, remove_default_tenant),
    ]
