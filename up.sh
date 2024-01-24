#! /bin/bash

source ./env/bin/activate
uwsgi --ini config/uwsgi.ini &
redis-server --port 6655 &
daphne -u /tmp/daphne.sock activities.asgi:application --access-log /home/websites/activities/logs/daphne.log &
celery -A activities beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &
celery -A activities worker --uid not_root &
nginx -c /home/websites/activities/config/nginx.conf

result=$(ps -e | grep turnserver)

if ! [[ $result ]]
then
        turnserver &
fi
