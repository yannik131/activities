#!/bin/bash
dir=${PWD}/backup/postgres_csv_linux
./save_database.sh
sudo -u postgres psql -c "drop database activities;"
sudo -u postgres psql -c "create database activities;"
sudo -u postgres psql -d activities -c "create extension hstore;"
python3 manage.py makemigrations account actions activity chat competitions scheduling usergroups vacancies wall
python3 manage.py migrate