from activities.celery import app
from .models import MultiplayerMatch
from account.models import User
from django.utils import timezone
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from datetime import datetime, timedelta
import re
import os
os.environ['MPLCONFIGDIR'] = '/tmp/'

import matplotlib.pyplot as plt


@app.task
def clearMultiplayerMatches():
    idle_delete_date = timezone.now()-MultiplayerMatch.IDLE_LIFESPAN
    running_delete_date = timezone.now()-MultiplayerMatch.RUNNING_LIFESPAN
    MultiplayerMatch.objects.filter(
        Q(in_progress=False, created__lt=idle_delete_date) | 
        Q(in_progress=True, created__lt=running_delete_date) | 
        Q(over=True, created__lt=idle_delete_date)).delete()
        
    delete_date = timezone.now()-User.GUEST_LIFESPAN
    User.objects.filter(is_guest=True, date_joined__lt=delete_date).delete()
    
@app.task 
def send_plot_email():
    yesterdays_clicks = plot_current_clicks()
    email = EmailMultiAlternatives(f"{datetime.now().strftime('%d.%m.')} - Current plot ({yesterdays_clicks})", "", 'myactivities.net@web.de', ['yannik131@web.de'])
    email.attach_file("logs/log.png")
    email.attach_file("logs/accepted_requests.txt")
    email.send()


def plot_current_clicks():
    with open("logs/uwsgi.log") as f:
        content = f.readlines()

    allowed = ['activity', 'multiplayer', 'competitions', 'usergroups', 'vacancies', 'account', 'character', 'notify', 'scheduling', 'wall']

    clicks = dict()
    parse_regex = "(.*), (.*): (?:GET|POST) \/(.*) -> \d+ms \((\d+)"
    banned = ["77.20.167.28", "34.140.175.20", "5.188.62.214"]
    accepted_requests = []
    for line in content:
        match = re.findall(parse_regex, line)
        if match:
            match = match[0]
            if match[3] == "302" or match[1] in banned or not match[2].endswith('/'):
                continue
            accepted_requests.append(line)
            dt = datetime.strptime(match[0], "%c")
            year_clicks = clicks.setdefault(dt.year, dict())
            month_clicks = year_clicks.setdefault(dt.month, dict())
            if dt.day not in month_clicks:
                month_clicks[dt.day] = 0
            month_clicks[dt.day] += 1
    with open("logs/accepted_requests.txt", "w") as file:
        for line in reversed(accepted_requests):
            file.write(line)
        file.close()
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