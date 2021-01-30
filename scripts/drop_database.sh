#!/bin/bash
# to be executed from the main directory where the manage.py is
# problems on mac: run brew services restart postgresql, maybe remove /usr/local/var/postgres and run initdb on that dir
# createuser root, alter role root with superuser, createdb activities
dir=scripts/csv
source scripts/comp.sh
find . -name migrations -type d -exec rm -rf {} \;
sudo $option psql -c "drop database activities;"
sudo $option psql -c "create database activities;"
sudo $option psql -d activities -c "create extension hstore;"
python3 manage.py makemigrations account activity chat competitions scheduling usergroups vacancies wall notify multiplayer
python3 manage.py migrate