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
        if self.activity.name == _('Durak'):
            if member_limit < 2 or member_limit > 4:
                raise forms.ValidationError(_("Unterstützt werden 2, 3 oder 4 Spieler"))
        elif self.activity.name == _('Skat'):
            if member_limit < 3 or member_limit > 4:
                raise forms.ValidationError(_("Unterstützt werden 3 oder 4 Spieler"))