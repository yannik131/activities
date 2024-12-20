from django.db import models
from usergroups.models import UserGroup
from django.utils.translation import gettext_lazy as _
from shared.shared import GERMAN_DATE_FMT
from account.models import User


class Appointment(models.Model):
    name = models.CharField(max_length=30, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=50)
    group = models.ForeignKey(UserGroup, related_name='appointments', on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_appointments')

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        if self.name:
            return self.name
        return _("Treffen am {start}").format(start=self.start_time)

    def start_time_formatted(self):
        return self.start_time.strftime(GERMAN_DATE_FMT)
        
    def get_absolute_url(self):
        return self.group.get_absolute_url()
        
    def verbose(self):
        return self.__str__()
