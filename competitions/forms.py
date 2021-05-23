from .models import Match, Tournament
from django import forms
from shared import shared
from account.models import User
from django.utils.translation import gettext_lazy as _
from account.models import Location


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
        location = Location.determine_from(city)
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
        self.instance.location = Location.determine_from(cd['location'])
        if cd['application_deadline'] > cd['start_time']:
            raise forms.ValidationError(_('Anmeldeschluss muss vor Turnierbeginn sein.'))
        return cd

class ScoreForm(forms.Form):
    def __init__(self, activity_name, ids, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activity_name = activity_name
        for user_id in ids:
            self.fields[user_id] = forms.FloatField(label=User.objects.get(id=user_id).username, initial=0)
            
    def clean(self):
        cd = super().clean()
        total = 0
        if self.activity_name == 'Schach':
            for key in self.fields:
                if cd[key] not in [0, 0.5, 1]:
                    raise forms.ValidationError(_('Erlaubte Werte: 0, 0.5 oder 1'))
                total += cd[key]
            if int(total) != 1:
                raise forms.ValidationError(_('Die Punkte addieren sich nicht zu 1'))
        elif self.activity_name == 'Doppelkopf':
            for key in self.fields:
                total += cd[key]
            if int(total) != 0:
                raise forms.ValidationError(_('Die Punkte addieren sich nicht zu 0'))

def make_matchup_score_form(matchup):
    fields = dict()
    for id in matchup:
        fields[id] = forms.FloatField(label=User.objects.get(id=id).username, initial=0, min_value=0)
    return type('MatchupScoreForm', (forms.BaseForm,), {'base_fields': fields})
