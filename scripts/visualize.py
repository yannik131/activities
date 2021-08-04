#!/usr/bin/python3

import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

os.environ['MPLCONFIGDIR'] = '/tmp/'

def plot_current_clicks():
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
            dt = datetime.strptime(match[0], "%c")
            year_clicks = clicks.setdefault(dt.year, dict())
            month_clicks = year_clicks.setdefault(dt.month, dict())
            if dt.day not in month_clicks:
                month_clicks[dt.day] = 0
            month_clicks[dt.day] += 1

    x = []
    y = []
    now = datetime.now()-timedelta(days=28)
    now_str = now.strftime('%d.%m.')
    result_str = ""
    total = 0
    for year in clicks:
        if now.year != year:
            continue
        for month in clicks[year]:
            if now.month != month:
                continue
            i = now.day
            for day in clicks[year][month]:
                while day > i:
                    x.append(i)
                    y.append(0)
                    i += 1
                if day < i:
                    continue
                count = clicks[year][month][day]
                total += count
                result_str += f"{day}.{month}.{year}: {count}\n"
                if count > 100:
                    result_str += ("#"*50)+"\n"
                x.append(i)
                y.append(clicks[year][month][day])
                i += 1
                now += timedelta(days=1)
    x = [str(v) for v in x]
    plt.bar(x, y, tick_label=x)
    plt.title(f"{now_str} - {datetime.now().strftime('%d.%m')} - Total: {total}")
    fig = plt.gcf()
    fig.set_size_inches(10, 5.5)
    fig.savefig("logs/log.png")
    return y[-1]

if __name__ == "__main__":
    plot_current_clicks()