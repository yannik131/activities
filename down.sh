#! /bin/bash

source ./env/bin/activate
ps -C "redis daphne nginx celery" -o pid= | xargs kill -9
uwsgi --stop /tmp/activities.pid