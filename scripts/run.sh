#!/bin/sh
# Подразумевана улазна тачка контејнера (Dockerfile `CMD`).
#
# Compose фајлови за развој и продукцију премошћују ову команду својим
# `command:`; голи `docker run` слике и самостални (standalone) стек користе
# ову скрипту. Идемпотентна је — безбедно се извршава при сваком старту.
set -e

# Сачекај да база прими конекције (management команда у репозиторијуму).
python manage.py wait_for_db

# Миграције СВИХ шема (public + тенанти). НЕ `migrate` — django-tenants.
python manage.py migrate_schemas --noinput

# Статички фајлови. `compress` није потребан (COMPRESS_OFFLINE=False).
python manage.py collectstatic --noinput

# Опциони bootstrap администратора из окружења (идемпотентно): креира налог
# само ако DJANGO_SUPERUSER_USERNAME/PASSWORD постоје и налог још не постоји.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput 2>/dev/null \
        && echo "Креиран суперкорисник $DJANGO_SUPERUSER_USERNAME." \
        || echo "Суперкорисник већ постоји или подаци непотпуни — прескачем."
fi

# WSGI сервер. Порт/радници су подесиви преко окружења. НЕ користимо
# scripts/gunicorn.conf.py (он је за bare-metal: bind :9000 + логови у
# /var/log/spc-registar/ којих нема у контејнеру).
exec gunicorn crkva.wsgi:application \
    --bind "0.0.0.0:${GUNICORN_PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}"
