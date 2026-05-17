#!/bin/bash
# Аутоматски backup базе података
# Покреће се преко cron-а: 0 3 * * * /root/projects/spc-registar/scripts/backup.sh

set -euo pipefail

BACKUP_DIR="/root/backups/spc-registar"
RETENTION_DAYS=30
DB_NAME="crkva_db"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Креирај директоријум ако не постоји
mkdir -p "${BACKUP_DIR}"

# pg_dump са компресијом
PGPASSWORD=postgres pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-privileges \
    | gzip > "${BACKUP_FILE}"

# Провери да ли је backup успешан
if [ -s "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date)] Backup успешан: ${BACKUP_FILE} (${SIZE})"
else
    echo "[$(date)] ГРЕШКА: Backup фајл је празан!" >&2
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# Обриши backup-е старије од RETENTION_DAYS дана
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Обрисани backup-и старији од ${RETENTION_DAYS} дана"
