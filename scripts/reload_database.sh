#!/bin/bash
# to be executed from the main directory where the manage.py is. Doesn't work if the database is used (i. e. by the development server)
# problems on mac: run brew services restart postgresql, maybe remove /usr/local/var/postgres and run initdb on that dir
# createuser root, alter role root with superuser, createdb activities
source scripts/comp.sh
find . -name migrations -type d -exec rm -rf {} \;
sudo $option psql -c "drop database activities;"
sudo $option psql -c "create database activities;"
sudo $option pg_restore -d activities backup/backup.db
python3 manage.py makemigrations account activity chat competitions scheduling usergroups vacancies wall notify multiplayer character
python3 manage.py migrate --fake 