#!/bin/sh
set -e

echo "--> Running Migrations..."
python manage.py migrate --noinput

echo "--> Collecting Staticfiles..."
python manage.py collectstatic --noinput

echo "--> Starting Celery Worker in background..."
celery -A config worker --loglevel=info &

echo "--> Starting Server with Daphne..."
# Указываем порт 8000 напрямую вместо переменной $PORT
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application