from activities.celery import app
from .models import MultiplayerMatch
from django.utils import timezone

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(5, clearMultiplayerMatches.s())
    
@app.task
def clearMultiplayerMatches():
    idle_delete_date = timezone.now()+MultiplayerMatch.IDLE_LIFESPAN
    MultiplayerMatch.objects.filter(in_progress=False, created__gt=idle_delete_date).delete()
    running_delete_date = timezone.now()+MultiplayerMatch.RUNNING_LIFESPAN
    MultiplayerMatch.objects.filter(in_progress=True, created__gt=running_delete_date).delete()