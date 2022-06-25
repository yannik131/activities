#!/usr/bin/python3

import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

with open("logs/uwsgi.log") as f:
    content = f.readlines()

allowed = ['activity', 'multiplayer', 'competitions', 'usergroups', 'vacancies', 'account', 'character', 'notify', 'scheduling', 'wall'];

clicks = dict()
parse_regex = "(.*), (.*): (?:GET|POST) /(.*) ->";
banned = ["77.20.167.28", "34.140.175.20"]

for line in content:
    match = re.findall(parse_regex, line)
    if match:
        match = match[0]
        if match[1] in banned or not match[2].endswith('/'):
            continue
        datetime = datetime.strptime(match[0], "%c")
        year_clicks = clicks.setdefault(datetime.year, dict())
        month_clicks = year_clicks.setdefault(datetime.month, dict())
        if datetime.day not in month_clicks:
            month_clicks[datetime.day] = 0
        month_clicks[datetime.day] += 1

x = []
y = []
i = 1
now = datetime.now()-timedelta(days=1)
for year in clicks:
    if now.year != year:
        continue
    for month in clicks[year]:
        if now.month != month:
            continue
        for day in clicks[year][month]:
            while day > i:
                x.append(i)
                y.append(0)
                i += 1
            count = clicks[year][month][day]
            print(f"{day}.{month}.{year}: {count}")
            if count > 100:
                print("#"*50)
            x.append(i)
            y.append(clicks[year][month][day])
            i += 1

plt.bar(x, y, tick_label=[str(i) for i in x])
fig = plt.gcf()
fig.set_size_inches(10, 5.5)
fig.savefig("logs/log.png")
