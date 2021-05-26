#! /bin/bash

uwsgi --ini config/uwsgi.ini &
redis --port 6655 &
daphne -u /tmp/daphne.sock activities.asgi:application &
nginx
celery -A activities beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &
celery -A activities worker --uid not_root &