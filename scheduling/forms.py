from django import forms
from .models import Appointment
from shared.shared import DATETIME_ATTRS
from django.utils.translation import gettext_lazy as _


class AppointmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].widget.attrs = DATETIME_ATTRS
        

    class Meta:
        model = Appointment
        fields = ('name', 'start_time', 'location')
        labels = {
            'name': _('Name'),
            'start_time': _('Datum & Uhrzeit'),
            'location': _('Ort')
        }
