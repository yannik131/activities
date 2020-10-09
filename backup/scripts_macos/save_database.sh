#!/bin/bash
dir=${PWD}/../postgres_csv_macos
psql -d activities -c "copy activity_category to '$dir/categories.csv' with (format csv); copy activity_activity to '$dir/activities.csv' with (format csv); copy account_user to '$dir/users.csv' with (format csv); copy account_user_user_permissions to '$dir/user_permissions.csv' with (format csv); copy account_location to '$dir/locations.csv' with (format csv);"
