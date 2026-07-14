"""Serbian-identifier rename: Tenant->Zakupac, Domain->Domen,
UserMembership->Clanstvo, and Clanstvo fields user/tenant/role ->
korisnik/parohija/uloga.

Model renames are state-only (db_table is pinned to the original names, so
no table is renamed). Field renames emit ALTER TABLE ... RENAME COLUMN and
preserve existing rows.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0002_remove_tenant_parohija_naziv"),
    ]

    operations = [
        migrations.RenameModel(old_name="Tenant", new_name="Zakupac"),
        migrations.RenameModel(old_name="Domain", new_name="Domen"),
        migrations.RenameModel(old_name="UserMembership", new_name="Clanstvo"),
        migrations.RenameField("clanstvo", "user", "korisnik"),
        migrations.RenameField("clanstvo", "tenant", "parohija"),
        migrations.RenameField("clanstvo", "role", "uloga"),
    ]
