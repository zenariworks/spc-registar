
@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:recreate_database
    
    REM migrate .dbf files to .sqlite database 
    python migrate-original-dbf-files-to-sqlite.py

    REM Remove migration files
    del /Q "crkva\registar\migrations\0*"
    
    REM Stop and remove db container
    docker stop crkva-db-1
    docker rm crkva-db-1

    REM Create database image: postgres:13-alpine
    docker compose run --rm app sh -c "python manage.py makemigrations && python manage.py migrate"
    
    docker compose run --rm app sh -c "python manage.py unosi"
    docker compose run --rm app sh -c "python manage.py unos_meseci"
    docker compose run --rm app sh -c "python manage.py migracija_slava"
    docker compose run --rm app sh -c "python manage.py migracija_svestenika"
    docker compose run --rm app sh -c "python manage.py unos_drzava"
    docker compose run --rm app sh -c "python manage.py migracija_ulica"
    docker compose run --rm app sh -c "python manage.py migracija_parohijana"
    docker compose run --rm app sh -c "python manage.py migracija_ukucana"
    docker compose run --rm app sh -c "python manage.py migracija_krstenja"
    docker compose run --rm app sh -c "python manage.py migracija_vencanja"

    REM Create super user, default uid/pwd: app/app
    REM NOTE: for email just press Enter...
    REM docker compose run --rm app sh -c "python manage.py createsuperuser"

    REM Run app
    REM docker stop crkva-app-1
    REM docker rm crkva-app-1
    REM docker compose build
    REM docker compose up 

ENDLOCAL
