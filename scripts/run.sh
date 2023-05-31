#!/bin/sh

set -e

ls -la /vol/
ls -la /vol/web

whoami

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate

python manage.py loaddata import_auth.json
python manage.py loaddata import_codetables.json
python manage.py loaddata import_metadata.json
python manage.py loaddata import_measures.json
python manage.py loaddata import_filters.json
python manage.py loaddata import_topicsets.json
python manage.py loaddata import_spatialdimensions.json

uwsgi --socket :9000 --workers 4 --master --enable-threads --module crkva.wsgi
