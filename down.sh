#! /bin/bash

ps -C "redis daphne uwsgi nginx celery" -o pid= | xargs kill -9
