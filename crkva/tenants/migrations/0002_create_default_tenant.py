"""Create the default Tenant + provision its Postgres schema.

Uses the historical Tenant model (via apps.get_model) so the INSERT only
references fields that exist at this point in the migration history — the
live model has fields added by later migrations (e.g. default_phone_region
in 0005) that would otherwise blow up a fresh migrate_schemas run on an
empty DB. The Postgres schema is created with a raw CREATE SCHEMA IF NOT
EXISTS; the subsequent migrate_schemas pass migrates TENANT_APPS into it.
"""

from django.conf import settings
from django.db import migrations


def create_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    UserMembership = apps.get_model("tenants", "UserMembership")
    User = apps.get_model(
        settings.AUTH_USER_MODEL.split(".")[0],
        settings.AUTH_USER_MODEL.split(".")[1],
    )

    tenant, _ = Tenant.objects.get_or_create(
        schema_name="crkva_sv_petke_cukarica",
        defaults={
            "naziv": "Парохија Чукарица",
            "parohija_naziv": "Парохија Чукарица",
            "is_active": True,
            "is_default": True,
        },
    )

    if not tenant.is_default:
        Tenant.objects.exclude(pk=tenant.pk).update(is_default=False)
        tenant.is_default = True
        tenant.save()

    # Provision the Postgres schema. The live Tenant model would have done
    # this via auto_create_schema=True during save(); the historical model
    # does not have that override, so we issue the CREATE explicitly. The
    # ongoing migrate_schemas pass then applies TENANT_APPS migrations into
    # the new schema, so we do not migrate it inline here.
    schema_editor.execute("CREATE SCHEMA IF NOT EXISTS crkva_sv_petke_cukarica")

    for user in User.objects.filter(is_active=True, is_staff=True):
        UserMembership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={"role": "admin", "is_default": True},
        )


def remove_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    Tenant.objects.filter(schema_name="crkva_sv_petke_cukarica").delete()
    schema_editor.execute("DROP SCHEMA IF EXISTS crkva_sv_petke_cukarica CASCADE")


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_tenant, remove_default_tenant),
    ]
