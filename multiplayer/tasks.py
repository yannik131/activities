from activities.celery import app
from .models import MultiplayerMatch
from account.models import User
from django.utils import timezone
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from datetime import datetime, timedelta, date
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
        Q(over=True, created__lt=idle_delete_date)).update(active=False)
        
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
    clicks = dict()
    parse_regex = "(.*), (.*): (?:GET|POST) \/(.*) -> \d+ms \((\d+)"
    banned = ["77.20.167.28", "34.140.175.20", "5.188.62.214"]
    accepted_requests = []
    today = date.today()
    start = today-timedelta(days=28)
    for line in content:
        match = re.findall(parse_regex, line)
        if match:
            match = match[0]
            if match[3] == "302" or match[1] in banned or not match[2].endswith('/'):
                continue
            dt = datetime.strptime(match[0], "%a %b %d %H:%M:%S %Y")
            d = date(dt.year, dt.month, dt.day)
            if d < start:
                continue
            accepted_requests.append(line)
            if not d in clicks:
                clicks[d] = 0
            clicks[d] += 1
    with open("logs/accepted_requests.txt", "w") as file:
        for line in reversed(accepted_requests):
            file.write(line)
        file.close()
    x = []
    y = []
    total = 0
    for day in clicks:
        x.append(day.strftime('%d.'))
        y.append(clicks[day])
        total += clicks[day]
    plt.xlabel("Tag")
    plt.ylabel("Aufrufe")
    plt.bar(x, y, tick_label=x)
    plt.title(f"{start.strftime('%d.%m.%y')} - {today.strftime('%d.%m.%y')} - Total: {total}")
    fig = plt.gcf()
    fig.set_size_inches(10, 5.5)
    fig.savefig("logs/log.png")
    plt.close()
    return y[-1]