#!/bin/bash
dir=${PWD}/backup/csv
source ${PWD}/backup/comp.sh
sudo $option psql -d activities -c "copy activity_category_translation from '$dir/category_translation.csv' with (format csv); copy activity_activity_translation from '$dir/activity_translation.csv' with (format csv); copy activity_category from '$dir/categories.csv' with (format csv); copy activity_activity from '$dir/activities.csv' with (format csv);"
