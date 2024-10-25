#!/bin/bash

set -x

function update_krstenja_vencanja(){

    python migrate-original-dbf-files-to-sqlite.py
    rm /mnt/c/crkva/registar/migrations/0*

    # stop and remove db container
    docker stop crkva-db-1
    docker rm crkva-db-1
    
    # update krstenja and vencanja
    docker compose run --rm app sh -c "python manage.py migracija_krstenja"
    docker compose run --rm app sh -c "python manage.py migracija_vencanja"
    
    # run app
    docker compose up 
}
readonly -f update_krstenja_vencanja

#run script
source myenv/bin/activate
update_krstenja_vencanja
