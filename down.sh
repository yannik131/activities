#! /bin/bash

ps -C "redis daphne uwsgi" -o pid= | xargs kill -9
nginx -s quit
