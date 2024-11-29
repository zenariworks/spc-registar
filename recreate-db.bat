
@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:recreate_database
    
    # migrate .dbf files to .sqlite database
    python migrate-original-dbf-files-to-sqlite.py

    # Remove migration files
    del /Q "crkva\registar\migrations\0*"
    
    # Stop and remove db container
    docker stop crkva-db-1
    docker rm crkva-db-1

    # Create database image: postgres:13-alpine
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

    # Create super user, default uid/pwd: app/app
    # NOTE: for email just press Enter...
    # docker compose run --rm app sh -c "python manage.py createsuperuser"

    # Run app
    # docker stop crkva-app-1
    # docker rm crkva-app-1
    # docker compose build
    # docker compose up

ENDLOCAL
