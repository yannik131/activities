#!/bin/bash
# to be executed from the main directory where the manage.py is
dir=${PWD}/backup/postgres_csv_linux
find . -name migrations -type d -exec rm -rf {} \;
sudo -u postgres psql -c "drop database activities;"
sudo -u postgres psql -c "create database activities;"
sudo -u postgres psql -d activities -c "create extension hstore;"
python3 manage.py makemigrations account activity chat competitions scheduling usergroups vacancies wall notify
python3 manage.py migrate