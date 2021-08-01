from matplotlib.pyplot import plot
from activities.celery import app
from .models import MultiplayerMatch
from account.models import User
from django.utils import timezone
from django.db.models import Q
from scripts.visualize import plot_current_clicks
from django.core.mail import EmailMultiAlternatives
from datetime import datetime

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
    plot_current_clicks()
    email = EmailMultiAlternatives(f"{datetime.now().strftime('%d.%m.')} - Current plot", "", 'myactivities.net@web.de', ['yannik131@web.de'])
    email.attach_file("logs/log.png")
    email.send()