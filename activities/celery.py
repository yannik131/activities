import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'activities.settings')
app = Celery('activities')
app.conf.broker_url = 'redis://localhost:6655'

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()