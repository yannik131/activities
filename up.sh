#! /bin/bash

ps -C uwsgi -o pid= | xargs kill -9
uwsgi --ini config/uwsgi.ini &
redis --port 6655 &
daphne -u /tmp/daphne.sock activities.asgi:application &
if [ -f /run/nginx.pid ]; then
	nginx -s reload
else
	nginx
fi
