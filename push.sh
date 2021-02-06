#! /bin/bash

git add .
now=$(date +"%d.%m.%y")
git commit -a -m "$now"
git push origin