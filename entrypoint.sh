#!/bin/sh
echo "Starting application..."

python manage.py migrate --noinput

if [ "$DJANGO_ENV" = "production" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
    echo "Running Gunicorn..."
    exec gunicorn hungwetips.wsgi:application --bind 0.0.0.0:8000 --workers 3
else
    echo "Running Django dev server..."
    exec python manage.py runserver 0.0.0.0:8000
fi
