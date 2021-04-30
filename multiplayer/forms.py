from django import forms
from .models import MultiplayerMatch
from django.utils.translation import gettext_lazy as _


class CreateMatchForm(forms.ModelForm):
    class Meta:
        model = MultiplayerMatch
        fields = ['member_limit']
        labels = {
            'member_limit': _('Spieleranzahl')
        }

    def clean(self):
        cd = super().clean()
        member_limit = cd['member_limit']
        if self.activity.german_name == 'Durak':
            if member_limit < 2 or member_limit > 4:
                raise forms.ValidationError(_("Unterstützt werden 2-4 Spieler"))
        elif self.activity.german_name == 'Poker':
            if member_limit < 2 or member_limit > 10:
                raise forms.ValidationError(_("Unterstützt werden 2-10 Spieler"))
        return cd
                
class PokerMatchForm(CreateMatchForm):
    blind_duration = forms.IntegerField(label=_('Blind-Dauer in Minuten'), initial=20)
    
    def clean(self):
        cd = super().clean()
        if int(cd['blind_duration']) < 5 or int(cd['blind_duration']) > 20:
            raise forms.ValidationError(_('Blind-Dauer muss zwischen 5 und 20 Minuten liegen'))
        return cd