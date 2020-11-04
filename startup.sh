#! /bin/bash

redis --port 6655 &
uwsgi -ini config/uwsgi.ini &
daphne -u /tmp/daphne.sock activities.asgi:application &
nginx -s reload
