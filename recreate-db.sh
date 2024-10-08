#!/bin/bash

usage() {
    echo -e "\e[1;33m\n Re-create databaase 'crkva-db-1' ( for dev purposes only ) \e[0m"
    echo "
 
 When database is re-created, all data is lost.
 It is necessary to recreate database when models are changed, 
 file E:\projects\hram-svete-petke\crkva\crkva\registar\migrations\0001_initial.py 

 Run this script only in development environment!
 
 usage:
 "
 echo -e "\e[1;33m    ./start.sh -h|--help         - print usage\e[0m"
 echo ""
 exit
}

#set -x


function recreate_database(){
    
    # stop and remove db container and image
    docker stop crkva-db-1
    docker rm crkva-db-1
    #docker rmi postgres:13-alpine
    #docker images
    
    # create database image: postgres:13-alpine
    docker compose run --rm app sh -c "python manage.py makemigrations && python manage.py migrate"
    
    # import test data (comment the following 2 lines in final migration script)
    # docker compose run --rm app sh -c "python manage.py unos_krstenja"
    # docker compose run --rm app sh -c "python manage.py unos_vencanja"

    docker compose run --rm app sh -c "python manage.py unosi"
    docker compose run --rm app sh -c "python manage.py unos_meseci"
    docker compose run --rm app sh -c "python manage.py migracija_slava"
    docker compose run --rm app sh -c "python manage.py migracija_svestenika"
    docker compose run --rm app sh -c "python manage.py unos_drzava"
    docker compose run --rm app sh -c "python manage.py migracija_ulica"
    docker compose run --rm app sh -c "python manage.py migracija_krstenja"

    # create super user, default uid/pwd: app/svpetka
    # NOTE: for email just press Enter...
    # docker compose run --rm app sh -c "python manage.py createsuperuser"

    # run app
    # docker compose up 

}
readonly -f recreate_database

#run script
recreate_database
