from django.db import models
from activity.models import Activity
from account.models import Location
from django.contrib.postgres.fields import HStoreField
from django.utils.translation import gettext_lazy as _

class Poll(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='polls')
    STATEMENT_CHOICES = (
        ('locations', _('Die besten Orte in %s für \"%s\"')),
        ()
    )
    statement = models.CharField(max_length=100, choices=STATEMENT_CHOICES)
    
    choices = HStoreField(default=dict)
    