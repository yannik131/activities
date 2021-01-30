source scripts/comp.sh
for app in "account" "usergroups" "vacancies" "wall" "competitions"
do
    python3 manage.py sqlsequencereset $app > scripts/sqlreset.sql
    sudo psql $option -d activities -f scripts/sqlreset.sql
done