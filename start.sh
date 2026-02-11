#!/bin/bash

#
# Skripta za izgradnju i pokretanje aplikacije.
#
# Primeri koriscenja:
#   ./start.sh                    # Pokreni sve (rebuild app + db + migrate + run)
#   ./start.sh --app              # Samo rebuild app kontejnera
#   ./start.sh --db               # Samo rebuild baze (migrations + load_dbf + migrate data)
#   ./start.sh --run              # Samo pokreni aplikaciju (load_dbf + krstenja/vencanja + up)
#   ./start.sh --home             # Koristi home WSL putanju za DBF fajlove
#   ./start.sh --zip /path/to.zip # Koristi ZIP arhivu za DBF fajlove
#

function show_usage() {
    echo "Usage: $0 [--app] [--db] [--run] [--home] [--zip <path>]"
    echo ""
    echo "Options:"
    echo "  --app   Rebuild app container"
    echo "  --db    Rebuild database (full migration)"
    echo "  --run   Quick start (load + krstenja/vencanja + up)"
    echo "  --home  Use home WSL path for DBF files"
    echo "  --zip   Use ZIP archive for DBF files"
    echo ""
    echo "If no options provided, runs: --app --db --run"
    exit 1
}

#set -x

# Initialize flags
APP_FLAG=false
DB_FLAG=false
RUN_FLAG=false
LOCATION="c"  # Default: church. Use '--home' for home WSL setup
ZIP_PATH=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --app) APP_FLAG=true ;;
        --db) DB_FLAG=true ;;
        --run) RUN_FLAG=true ;;
        --home) LOCATION="h" ;;
        --zip)
            shift
            ZIP_PATH="$1"
            ;;
        --help|-h) show_usage ;;
        *) show_usage ;;
    esac
    shift
done

# If no arguments provided, enable all
if [ "$APP_FLAG" = false ] && [ "$DB_FLAG" = false ] && [ "$RUN_FLAG" = false ]; then
    echo "No arguments provided. Running full build (--app --db --run)..."
    APP_FLAG=true
    DB_FLAG=true
    RUN_FLAG=true
fi

# Function to get load_dbf command based on location/zip
function get_load_dbf_cmd() {
    if [ -n "$ZIP_PATH" ]; then
        echo "python manage.py load_dbf --src_zip '${ZIP_PATH}'"
    elif [ "$LOCATION" = "h" ]; then
        # WSL setup (home)
        echo "python manage.py load_dbf --src_dir '/mnt/e/projects/hram-svete-petke/old-app/HramSP/dbf'"
    else
        # WSL setup (crkva)
        echo "python manage.py load_dbf --src_dir '/mnt/c/HramSP/dbf'"
    fi
}

# Function to check if a Docker container exists, stop and delete it
function delete_docker_container() {
    local CONTAINER_NAME="$1"

    if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
        if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
            echo "Stopping container '${CONTAINER_NAME}'..."
            docker stop "${CONTAINER_NAME}"
        fi
        echo "Removing container '${CONTAINER_NAME}'..."
        docker rm "${CONTAINER_NAME}"
        echo "Container '${CONTAINER_NAME}' has been removed."
    else
        echo "Container '${CONTAINER_NAME}' does not exist."
    fi
}

function delete_migrations() {
    DIRECTORY="crkva/registar/migrations"
    FILE_PATTERN="0*"

    if [ -d "${DIRECTORY}" ]; then
        if ls "${DIRECTORY}/${FILE_PATTERN}" 1> /dev/null 2>&1; then
            echo "Deleting files matching '${FILE_PATTERN}' in '${DIRECTORY}'..."
            rm "${DIRECTORY}/${FILE_PATTERN}"
            echo "Files deleted."
        else
            echo "No files matching '${FILE_PATTERN}' found in '${DIRECTORY}'."
        fi
    else
        echo "Directory '${DIRECTORY}' does not exist."
    fi
}

function rebuild_app() {
    APP_CONTAINER_NAME="crkva-app-1"
    delete_docker_container "${APP_CONTAINER_NAME}"
    docker compose build
}

function recreate_database() {
    pip install --upgrade -r requirements.txt

    delete_migrations

    DB_CONTAINER_NAME="crkva-db-1"
    delete_docker_container "${DB_CONTAINER_NAME}"

    # Create database and run Django migrations
    docker compose run --rm app sh -c "python manage.py makemigrations && python manage.py migrate"

    # Load DBF files into staging tables
    LOAD_CMD=$(get_load_dbf_cmd)
    docker compose run --rm app sh -c "${LOAD_CMD}"

    # Run all data migrations
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
}

function quick_run() {
    # Load DBF and run only krstenja/vencanja migrations, then start app
    LOAD_CMD=$(get_load_dbf_cmd)
    docker compose run --rm app sh -c "${LOAD_CMD}"
    docker compose run --rm app sh -c "python manage.py migracija_krstenja"
    docker compose run --rm app sh -c "python manage.py migracija_vencanja"
    docker compose up
}

#
# Run script
#
if [ "$APP_FLAG" = true ]; then
    echo "=== Building the app container 'crkva-app-1'... ==="
    rebuild_app
fi

if [ "$DB_FLAG" = true ]; then
    echo "=== Building the database container 'crkva-db-1'... ==="
    recreate_database
fi

if [ "$RUN_FLAG" = true ]; then
    if [ "$DB_FLAG" = false ]; then
        # Quick run - only load recent data and start
        echo "=== Quick start (load + krstenja/vencanja)... ==="
        quick_run
    else
        # Full run after db rebuild
        echo "=== Starting application... ==="
        docker compose up
    fi
fi
