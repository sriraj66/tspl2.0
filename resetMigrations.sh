rm -r ./core/migrations db.sqlite3; python3 manage.py makemigrations core;python3 manage.py migrate

echo "Creating super User"
DJANGO_SUPERUSER_PASSWORD=admin python3 manage.py createsuperuser --username admin --email admin@gmail.com --noinput
