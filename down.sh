#! /bin/bash

ps -C "redis daphne uwsgi nginx" -o pid= | xargs kill -9
