"""Create the default Tenant ('Парохија Чукарица') and bind any existing
admin user(s) to it. Idempotent — safe to re-run.
"""

from django.conf import settings
from django.db import migrations


def create_default_tenant(apps, schema_editor):
    Eparhija = apps.get_model("registar", "Eparhija")
    CrkvenaOpstina = apps.get_model("registar", "CrkvenaOpstina")
    Parohija = apps.get_model("registar", "Parohija")
    Tenant = apps.get_model("tenants", "Tenant")
    UserMembership = apps.get_model("tenants", "UserMembership")
    User = apps.get_model(
        settings.AUTH_USER_MODEL.split(".")[0], settings.AUTH_USER_MODEL.split(".")[1]
    )

    # Find or create the org hierarchy down to Parohija.
    eparhija, _ = Eparhija.objects.get_or_create(
        naziv="београдско-карловачка",
    )
    crkvena_opstina, _ = CrkvenaOpstina.objects.get_or_create(
        naziv="Чукарица",
        defaults={"eparhija": eparhija},
    )
    parohija, _ = Parohija.objects.get_or_create(
        naziv="Парохија Чукарица",
        defaults={"crkvena_opstina": crkvena_opstina},
    )

    # Find or create the Tenant.
    tenant, created = Tenant.objects.get_or_create(
        parohija=parohija,
        defaults={
            "naziv": "Парохија Чукарица",
            "schema_name": "tenant_cukarica",
            "is_active": True,
            "is_default": True,
        },
    )
    if not created and not tenant.is_default:
        # Make sure exactly one default exists.
        Tenant.objects.exclude(pk=tenant.pk).update(is_default=False)
        tenant.is_default = True
        tenant.save()

    # Bind every existing superuser/staff user to the default tenant as admin.
    for user in User.objects.filter(is_active=True).filter(is_staff=True):
        UserMembership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={"role": "admin", "is_default": True},
        )


def remove_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    Tenant.objects.filter(schema_name="tenant_cukarica").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0001_initial"),
        ("registar", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_tenant, remove_default_tenant),
    ]
