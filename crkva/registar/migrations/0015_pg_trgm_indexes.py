"""Install pg_trgm + GIN trigram indexes on the hot icontains columns.

Django's __icontains lookup compiles to SQL ILIKE '%foo%', which the plain
btree indexes (with or without varchar_pattern_ops) cannot accelerate.
pg_trgm's gin_trgm_ops operator class indexes character trigrams so that
arbitrary substring ILIKE patterns run as Bitmap Index Scans instead of
Seq Scans.

Indexed columns are the ones the app calls __icontains on most:
  - Osoba.ime / prezime          → search_view, parohijan select2 widget
  - Adresa.ulica / mesto         → adresa select2 widget, address search
  - Hram.naziv                   → hram select2 widget

pg_trgm extension is installed once into the public schema (idempotent),
shared by all tenants. The GIN indexes live in each tenant's schema (this
runs as a per-tenant migration via django-tenants).
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registar", "0014_alter_svestenik_options_alter_adresa_mesto_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Osoba: ime + prezime are searched via __icontains across multiple
        # views (search_view, every select2 widget that uses OsobaSelect2Widget).
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS osoba_ime_trgm_idx "
                "ON osobe USING gin (ime public.gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX IF EXISTS osoba_ime_trgm_idx;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS osoba_prezime_trgm_idx "
                "ON osobe USING gin (prezime public.gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX IF EXISTS osoba_prezime_trgm_idx;",
        ),
        # Adresa: ulica + mesto are the two search fields on every adresa widget.
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS adresa_ulica_trgm_idx "
                "ON adrese USING gin (ulica public.gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX IF EXISTS adresa_ulica_trgm_idx;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS adresa_mesto_trgm_idx "
                "ON adrese USING gin (mesto public.gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX IF EXISTS adresa_mesto_trgm_idx;",
        ),
        # Hram: naziv is the single search field on HramSelect2Widget.
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS hram_naziv_trgm_idx "
                "ON hramovi USING gin (naziv public.gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX IF EXISTS hram_naziv_trgm_idx;",
        ),
    ]
