#!/bin/bash

#
# Ova skripta ce migrirati tabelu krstena i vencanja i pokrenuti aplikaciju kojoj se pristupa preko http://localhost:8000
#

set -x

python migrate-original-dbf-files-to-sqlite.py

docker compose run --rm app sh -c "python manage.py migracija_krstenja"
docker compose run --rm app sh -c "python manage.py migracija_vencanja"

# run both db and app containers
# docker compose up -d 
docker compose up

