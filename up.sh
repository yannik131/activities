#! /bin/bash

export DJANGO_SETTINGS_MODULE=activities.settings.pro
ps -C "uwsgi nginx" -o pid= | xargs kill -9
uwsgi --ini config/uwsgi.ini &
redis --port 6655 &
daphne -u /tmp/daphne.sock activities.asgi:application &
nginx
celery -A activities beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &
celery -A activities worker &