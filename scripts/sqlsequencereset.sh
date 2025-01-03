#! /bin/bash
source scripts/comp.sh
for app in "account" "usergroups" "vacancies" "wall" "competitions" "multiplayer" "character"
do
    python3 manage.py sqlsequencereset $app > scripts/sqlreset.sql
    sudo $option psql -d activities -f scripts/sqlreset.sql
done