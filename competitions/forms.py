from .models import Match, Tournament
from django import forms
from shared import shared
from datetime import datetime


class MatchForm(forms.ModelForm):

    location = forms.CharField(label='Austragungsort (Stadt)')

    class Meta:
        model = Match

        fields = ('start_time', 'public', 'address', 'format')
        labels = {
            'start_time': 'Wann findet das Match statt?',
            'public': 'Soll das Match öffentlich unter Matches & Turniere sichtbar sein?',
            'address': 'Wo genau findet das Match statt?',
            'format': 'Bitte beschreiben Sie kurz die Spielregeln und das Format des Matches'
        }
        widgets = {
            'format': forms.Textarea
        }

    def clean(self):
        cd = super().clean()
        city = cd['location']
        location = shared.get_location(city)
        self.instance.location = location
        return cd


class TournamentForm(forms.ModelForm):

    location = forms.CharField(label='Austragungsort (Stadt)')

    class Meta:
        model = Tournament
        fields = ['address', 'starting_time', 'application_deadline', 'max_members', 'fixed_number_of_rounds', 'format']
        labels = {
            'address': 'Adresse (falls das Turnier an einem einzigen Ort stattfindet, sonst leer lassen)',
            'starting_time': 'Turnierbeginn',
            'application_deadline': 'Anmeldeschluss',
            'max_members': 'Maximale Teilnehmeranzahl (leer lassen für kein Limit)',
            'fixed_number_of_rounds': 'Rundenanzahl (leer lassen für automatische Ermittlung)',
            'format': 'Turnierformat und weitere Informationen'
        }

    def clean(self):
        cd = super().clean()
        self.instance.location = shared.get_location(cd['location'])
        if cd['application_deadline'] > cd['starting_time']:
            raise forms.ValidationError('Anmeldeschluss muss vor Turnierbeginn sein.')
        return cd
