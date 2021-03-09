from django import forms
from .models import Appointment
from django.utils import timezone
from shared.shared import GERMAN_DATE_FMT
from django.utils.translation import gettext_lazy as _


class AppointmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].widget.attrs['class'] = 'datetime'
        

    class Meta:
        model = Appointment
        fields = ('name', 'start_time', 'location')
        labels = {
            'name': _('Name'),
            'start_time': _('Datum & Uhrzeit'),
            'location': _('Ort')
        }

