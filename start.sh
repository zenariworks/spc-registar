#!/bin/bash

#
# Ova skripta ce migrirati tabelu krstena i vencanja i pokrenuti aplikaciju kojoj se pristupa preko http://localhost:8000
#

#set -x

# WSL setup (crkva)
python migrate-original-dbf-files-to-sqlite.py --src_dir "/mnt/c/HramSP/dbf" --dest_dir "crkva/fixtures"

# WSL setup (home)
#python migrate-original-dbf-files-to-sqlite.py --src_dir "/mnt/e/projects/hram-svete-petke/resources/dbf" --dest_dir "crkva/fixtures"

docker compose run --rm app sh -c "python manage.py migracija_krstenja"
docker compose run --rm app sh -c "python manage.py migracija_vencanja"

# run both db and app containers
# docker compose up -d
docker compose up
