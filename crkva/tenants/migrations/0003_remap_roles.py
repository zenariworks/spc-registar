"""Remap UserMembership.role: member→kancelarija, viewer→pregled.

Replaces the old admin/member/viewer choices with
admin/kancelarija/svestenstvo/pregled. Existing 'admin' rows stay.
"""

from django.db import migrations, models


def forward(apps, schema_editor):
    Membership = apps.get_model("tenants", "UserMembership")
    Membership.objects.filter(role="member").update(role="kancelarija")
    Membership.objects.filter(role="viewer").update(role="pregled")


def backward(apps, schema_editor):
    Membership = apps.get_model("tenants", "UserMembership")
    Membership.objects.filter(role="kancelarija").update(role="member")
    Membership.objects.filter(role="svestenstvo").update(role="member")
    Membership.objects.filter(role="pregled").update(role="viewer")


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0002_create_default_tenant"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
        migrations.AlterField(
            model_name="usermembership",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Администратор"),
                    ("kancelarija", "Канцеларија"),
                    ("svestenstvo", "Свештенство"),
                    ("pregled", "Преглед"),
                ],
                default="pregled",
                max_length=20,
            ),
        ),
    ]
