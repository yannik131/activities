q#!/bin/bash
dir=${PWD}/backup/postgres_csv_linux
sudo -u postgres psql -d activities -c "copy activity_category_translation to '$dir/category_translation.csv' with (format csv); copy activity_activity_translation to '$dir/activity_translation.csv' with (format csv); copy activity_category to '$dir/categories.csv' with (format csv); copy activity_activity to '$dir/activities.csv' with (format csv); copy account_user to '$dir/users.csv' with (format csv); copy account_location to '$dir/locations.csv' with (format csv);"
