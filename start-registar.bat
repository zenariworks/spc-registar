@echo on

REM ova skripta ce migrirati tabelu krstena i vencanja i pokrenuti aplikaciju
REM kojoj se pristupa preko http://localhost:8000
REM tako da sve jednim klikom bude spremno za stampu

REM wsl -e bash -c "/mnt/c/crkva/recreate-db-krstenja-vencanja.sh"

REM docker desktop mora biti pokrenut. Napravio sam da se startuje sa windowsom

python migrate-original-dbf-files-to-sqlite.py

docker compose run --rm app sh -c "python manage.py migracija_krstenja"
docker compose run --rm app sh -c "python manage.py migracija_vencanja"

docker compose up -d 

start microsoft-edge:http://localhost:8000

