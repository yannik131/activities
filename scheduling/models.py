from django.db import models
from usergroups.models import UserGroup
from shared.shared import GERMAN_DATE_FMT


class Appointment(models.Model):
    name = models.CharField(max_length=30, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=50)
    group = models.ForeignKey(UserGroup, related_name='appointments', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        if self.name:
            return self.name
        return _("Treffen am {start}").format(start=self.start_time)

    def start_time_formatted(self):
        return self.start_time.strftime(GERMAN_DATE_FMT)
