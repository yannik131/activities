from .models import Match, Tournament
from django import forms
from shared import shared
from account.models import User
from django.utils.translation import gettext_lazy as _


class MatchForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].widget.attrs['class'] = 'datetime'
    location = forms.CharField(label=_('Austragungsort (Stadt)'))

    class Meta:
        model = Match

        fields = ('start_time', 'public', 'address', 'format')
        labels = {
            'start_time': _('Wann findet das Match statt?'),
            'public': _('Soll das Match öffentlich unter Matches & Turniere sichtbar sein?'),
            'address': _('Wo genau findet das Match statt?'),
            'format': _('Bitte beschreiben Sie kurz die Spielregeln und das Format des Matches'),
            'for_groups': _('Mannschaftsspiel')
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].widget.attrs['class'] = 'datetime'
        self.fields['application_deadline'].widget.attrs['class'] = 'datetime'
        
    location = forms.CharField(label=_('Austragungsort (Stadt)'))

    class Meta:
        model = Tournament
        fields = ['title', 'address', 'start_time', 'application_deadline', 'format']
        labels = {
            'title': _('Titel des Turniers'),
            'address': _('Adresse (falls das Turnier an einem einzigen Ort stattfindet, sonst leer lassen)'),
            'start_time': _('Turnierbeginn'),
            'application_deadline': _('Anmeldeschluss'),
            'max_members': _('Maximale Teilnehmeranzahl (leer lassen für kein Limit)'),
            'fixed_number_of_rounds': _('Rundenanzahl (leer lassen für automatische Ermittlung)'),
            'format': _('Turnierformat und weitere Informationen'),
            'for_groups': _('Mannschaftsspiel')
        }

    def clean(self):
        cd = super().clean()
        self.instance.location = shared.get_location(cd['location'])
        if cd['application_deadline'] > cd['start_time']:
            raise forms.ValidationError(_('Anmeldeschluss muss vor Turnierbeginn sein.'))
        return cd


def make_matchup_score_form(matchup):
    fields = dict()
    for id in matchup:
        fields[id] = forms.IntegerField(label=User.objects.get(id=id).username, initial=0)
    return type('MatchupScoreForm', (forms.BaseForm,), {'base_fields': fields})
