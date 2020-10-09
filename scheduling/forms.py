from django import forms
from .models import Appointment
from django.utils import timezone
from shared.shared import GERMAN_DATE_FMT


class AppointmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].initial = timezone.now().strftime(GERMAN_DATE_FMT)

    class Meta:
        model = Appointment
        fields = ('name', 'start_time', 'location')
        labels = {
            'name': 'Name',
            'start_time': 'Datum & Uhrzeit',
            'location': 'Ort'
        }

