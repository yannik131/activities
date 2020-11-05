#! /bin/bash

ps -C uwsgi -o pid= | xargs kill -9
uwsgi --ini config/uwsgi.ini &
nginx -s reload
