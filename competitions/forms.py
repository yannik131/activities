from .models import Match
from django import forms
from account.models import User, Location
import shared


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
        try:
            location = Location.objects.get(city=city)
        except Location.DoesNotExist:
            location = shared.get_location(city)
        self.instance.location = location
        return cd
