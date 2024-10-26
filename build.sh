#!/bin/bash

#
# This script is used to recreate the database from the original dbf files and rebuild the app. 
#

set -x

# Function to check if a Docker container exists, stop and delete it
function delete_docker_container() {
    local CONTAINER_NAME="$1"

    # Check if the container exists
    if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
        # Stop the container if it is running
        if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
            echo "Stopping container '${CONTAINER_NAME}'..."
            docker stop "${CONTAINER_NAME}"
        fi

        # Remove the container
        echo "Removing container '${CONTAINER_NAME}'..."
        docker rm "${CONTAINER_NAME}"
        echo "Container '${CONTAINER_NAME}' has been removed."
    else
        echo "Container '${CONTAINER_NAME}' does not exist."
    fi
}
readonly -f delete_docker_container

function delete_migrations() {
    # Directory and file pattern
    DIRECTORY="crkva/registar/migrations"
    FILE_PATTERN="0*"

    # Check if the directory exists
    if [ -d "${DIRECTORY}" ]; then
        # Check for files matching the pattern
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
readonly -f delete_migrations

function recreate_database(){

    python migrate-original-dbf-files-to-sqlite.py

    # remove migration files
    delete_migrations
    
    # stop and remove db container and image if exist
    DB_CONTAINER_NAME="crkva-db-1"
    delete_docker_container "${DB_CONTAINER_NAME}"

    #docker rmi postgres:13-alpine
    #docker images
    
    # create database image: postgres:13-alpine
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

    # create super user, default uid/pwd: app/app
    # NOTE: for email just press Enter...
    # docker compose run --rm app sh -c "python manage.py createsuperuser"
}
readonly -f recreate_database

function rebuild_app(){

    # stop and remove app container if exist
    APP_CONTAINER_NAME="crkva-app-1"
    delete_docker_container "${APP_CONTAINER_NAME}"
   
    docker compose build
    
    # run both containers 
    # docker compose up 
}
readonly -f rebuild_app

#
#run script
#
recreate_database
rebuild_app
