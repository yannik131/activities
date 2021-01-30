#!/bin/bash
dir=${PWD}/scripts/csv
source ${PWD}/scripts/comp.sh
sudo $option psql -d activities -c "copy activity_category_translation to '$dir/category_translation.csv' with (format csv); copy activity_activity_translation to '$dir/activity_translation.csv' with (format csv); copy activity_category to '$dir/categories.csv' with (format csv); copy activity_activity to '$dir/activities.csv' with (format csv);"
