"""pg_trgm GIN trigram indexes for fast __icontains name/address search.

Salvaged from the obsolete refactor/db-indexes-audit branch (PR #209): the
model-level btree indexes from that audit already landed in main via the
squashed 0001 migration, but the pg_trgm trigram indexes (originally its
migration 0015) were never carried over.

Django btree indexes cannot accelerate ILIKE '%foo%' (the SQL Django emits
for __icontains, used heavily by the global search over osobe/adrese/hramovi).
pg_trgm GIN indexes let the planner switch to a Bitmap Index Scan instead of a
Seq Scan on those hot columns. Each statement is idempotent (IF NOT EXISTS)
and reversible.

registar is a TENANT app, so this runs once per tenant schema: the unqualified
CREATE INDEX targets the tenant's own table, while the extension is created
once in the shared public schema (IF NOT EXISTS makes repeats a no-op).
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "registar",
            "0001_initial_squashed_0014_alter_svestenik_options_alter_adresa_mesto_and_more",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;",
            # Dropping pg_trgm could break other databases sharing the cluster.
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS osoba_ime_trgm_idx ON osobe USING gin (ime public.gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS osoba_ime_trgm_idx;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS osoba_prezime_trgm_idx ON osobe USING gin (prezime public.gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS osoba_prezime_trgm_idx;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS adresa_ulica_trgm_idx ON adrese USING gin (ulica public.gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS adresa_ulica_trgm_idx;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS adresa_mesto_trgm_idx ON adrese USING gin (mesto public.gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS adresa_mesto_trgm_idx;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS hram_naziv_trgm_idx ON hramovi USING gin (naziv public.gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS hram_naziv_trgm_idx;",
        ),
    ]
