#!/bin/bash
dir=${PWD}/../postgres_csv
psql -c "drop database activities;"
psql -c "create database activities;"
python3 $dir/../manage.py makemigrations account activity chat competitions scheduling usergroups vacancies wall
python3 $dir/../manage.py migrate
psql -d activities -c "copy activity_category from '$dir/categories.csv' with (format csv); copy activity_activity from '$dir/activities.csv' with (format csv); copy account_location from '$dir/locations.csv' with (format csv); copy account_user from '$dir/users.csv' with (format csv); copy account_user_user_permissions from '$dir/user_permissions.csv' with (format csv);"
