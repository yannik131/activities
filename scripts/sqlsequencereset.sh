source scripts/comp.sh
for app in "account" "usergroups" "vacancies" "wall" "competitions"
do
    python3 manage.py sqlsequencereset $app > scripts/sqlreset.sql
    sudo $option psql -d activities -f scripts/sqlreset.sql
done