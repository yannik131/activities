#! /bin/bash

ps -C "uwsgi nginx" -o pid= | xargs kill -9
uwsgi --ini config/uwsgi.ini &
redis --port 6655 &
daphne -u /tmp/daphne.sock activities.asgi:application &
nginx
sudo -u not_root celery -A activities beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &
sudo -u not_root celery -A activities worker &