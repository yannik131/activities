from activities.celery import app
from .models import MultiplayerMatch
from django.utils import timezone
from django.db.models import Q

@app.task
def clearMultiplayerMatches():
    idle_delete_date = timezone.now()-MultiplayerMatch.IDLE_LIFESPAN
    running_delete_date = timezone.now()-MultiplayerMatch.RUNNING_LIFESPAN
    MultiplayerMatch.objects.filter(
        Q(in_progress=False, created__lt=idle_delete_date) | 
        Q(in_progress=True, created__lt=running_delete_date) | 
        Q(over=True, created__lt=idle_delete_date)).delete()