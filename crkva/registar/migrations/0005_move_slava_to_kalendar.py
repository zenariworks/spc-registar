"""Move Slava from registar (per-tenant) to kalendar (shared/public schema).

Strategy
--------
1. Drop Domacinstvo.slava + HistoricalDomacinstvo.slava (tenant-side FKs to
   ``registar.slava``).
2. Drop the ``registar.Slava`` model (and the ``slave`` DB table within each
   tenant schema). The new canonical ``slave`` table is created by the new
   ``kalendar`` app in the public schema (see ``kalendar/migrations/0001_initial.py``).
3. Re-add Domacinstvo.slava and HistoricalDomacinstvo.slava as ForeignKeys to
   ``kalendar.Slava`` with ``db_constraint=False`` — Postgres FKs cannot cross
   schemas in a django-tenants setup, but Django's Python-level relationship
   still works (queries, select_related, admin, forms).

Note: this migration drops tenant-side Slava data. The instructions for this
refactor are to wipe + reimport, so the data loss is intentional and the
``unos_slava`` / ``migracija_slava`` commands repopulate from fixtures/DBF.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registar", "0004_adresa_unique_adresa_normalized"),
        ("kalendar", "0001_initial"),
    ]

    operations = [
        # 1. Drop the FK columns that point at registar.slava.
        migrations.RemoveField(
            model_name="domacinstvo",
            name="slava",
        ),
        migrations.RemoveField(
            model_name="historicaldomacinstvo",
            name="slava",
        ),
        # 2. Drop the per-tenant Slava model/table.
        migrations.DeleteModel(
            name="Slava",
        ),
        # 3. Re-add the FK, this time targeting kalendar.Slava in public schema.
        #    db_constraint=False — cross-schema FKs cannot be enforced at the
        #    Postgres level in a django-tenants setup.
        migrations.AddField(
            model_name="domacinstvo",
            name="slava",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="kalendar.slava",
                verbose_name="слава домаћинства",
            ),
        ),
        migrations.AddField(
            model_name="historicaldomacinstvo",
            name="slava",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="kalendar.slava",
                verbose_name="слава домаћинства",
            ),
        ),
    ]
