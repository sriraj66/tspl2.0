#!/bin/sh

chmod +x ./wait_for_db.sh 
./wait_for_db.sh db:5432 -t 15

echo "waiting 5 sec"
sleep 5
python3 manage.py migrate --no-input
python3 manage.py makemigrations core --no-input
# python3 manage.py makemigrations --no-input
python3 manage.py migrate --no-input
python3 manage.py collectstatic --no-input

DJANGO_SUPERUSER_PASSWORD=$SUPER_USER_PASSWORD python3 manage.py createsuperuser --username $SUPER_USER_NAME --email $SUPER_USER_EMAIL --noinput

gunicorn -b 0.0.0.0:8000 backend.wsgi 
