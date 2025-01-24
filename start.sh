#!/bin/bash

#
# Ova skripta ce migrirati tabelu krstena i vencanja i pokrenuti aplikaciju kojoj se pristupa preko http://localhost:8000
#

#set -x

# Default location is church [-c]. Use '-h' for 'home' setup

location="c"

# Parse command line arguments
while getopts "hc" opt; do
 case $opt in
   h) location="h" ;;
   c) location="c" ;;
   *) echo "Usage: $0 [-h] [-c]"; exit 1 ;;
 esac
done

if [ "$location" = "h" ]; then
  # WSL setup (home)
  python migrate-original-dbf-files-to-sqlite.py --src_dir "/mnt/e/projects/hram-svete-petke/resources/dbf" --dest_dir "crkva/fixtures" 
else
  # WSL setup (crkva)
  python migrate-original-dbf-files-to-sqlite.py --src_dir "/mnt/c/HramSP/dbf" --dest_dir "crkva/fixtures"
fi


docker compose run --rm app sh -c "python manage.py migracija_krstenja"
docker compose run --rm app sh -c "python manage.py migracija_vencanja"

# run both db and app containers
# docker compose up -d
docker compose up
