from django import forms
from .models import MultiplayerMatch
from django.utils.translation import gettext_lazy as _

class MultiplayerMatchForm(forms.ModelForm):
    class Meta:
        model = MultiplayerMatch
        fields = ['member_limit']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member_limit'].widget = forms.HiddenInput()
        

class PokerMatchForm(MultiplayerMatchForm):
    blind_duration = forms.IntegerField(label=_('Blind-Dauer in Minuten'), initial=20)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member_limit'].initial = 10
    
    def clean(self):
        cd = super().clean()
        if int(cd['blind_duration']) < 5 or int(cd['blind_duration']) > 20:
            raise forms.ValidationError(_('Blind-Dauer muss zwischen 5 und 20 Minuten liegen'))
        return cd
        
class DokoMatchForm(MultiplayerMatchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member_limit'].initial = 4
    
    without_nines = forms.BooleanField(label=_('Ohne Neunen'), required=False)
    round_count = forms.ChoiceField(label=_('Rundenanzahl'), choices=[(i, str(i)) for i in range(1, 11)], initial="5", required=True)
    poverty = forms.BooleanField(label=_('Armut'), required=False)
    
class DurakMatchForm(MultiplayerMatchForm):
    all_help = forms.BooleanField(label=_('Jeder kann dazuschmeißen'), required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member_limit'].initial = 5