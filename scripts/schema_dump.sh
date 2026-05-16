#!/bin/bash
# Dump schema for dbdiagram.io import.
#
# Tenant-aware: per-tenant tables live in `crkva_sv_petke_cukarica` schema by
# default; SHARED tenants_* tables live in `public`. Override the
# tenant schema with TENANT_SCHEMA=tenant_xxx if needed.
#
# Usage: ./scripts/schema_dump.sh
#        TENANT_SCHEMA=tenant_vracar ./scripts/schema_dump.sh

set -euo pipefail

TENANT_SCHEMA=${TENANT_SCHEMA:-crkva_sv_petke_cukarica}

# Per-tenant tables (one set per tenant schema)
TENANT_TABLES=(
    adrese crkvene_opstine domacinstva eparhije hramovi
    krstenja narodnosti osobe parohije slave
    svestenici ukucani vencanja veroispovesti zanimanja
)

# Shared tables (always in public)
SHARED_TABLES=(
    tenants_tenant
    tenants_domain
    tenants_user_membership
)

TABLE_ARGS=
for t in "${TENANT_TABLES[@]}"; do
    TABLE_ARGS+=" -t ${TENANT_SCHEMA}.${t}"
done
for t in "${SHARED_TABLES[@]}"; do
    TABLE_ARGS+=" -t public.${t}"
done

PGPASSWORD=${DB_PASS:-postgres} pg_dump \
    -h "${DB_HOST:-localhost}" \
    -p "${DB_PORT:-5432}" \
    -U "${DB_USER:-postgres}" \
    -d "${DB_NAME:-crkva_db}" \
    --schema-only --no-owner --no-privileges \
    $TABLE_ARGS \
    > schema.sql

FK_COUNT=$(grep -c 'FOREIGN KEY' schema.sql || true)
echo "Schema dumped to schema.sql (${FK_COUNT} FK constraints, tenant=${TENANT_SCHEMA})"
