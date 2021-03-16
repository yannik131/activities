from django import forms
from django.contrib.auth import get_user_model
from account.models import User
from .utils import get_location
from django.utils.translation import gettext_lazy as _


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label=_('Passwort'),
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Passwort (erneut)'),
                                widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('username',)
        labels = {
            'sex': _('Geschlecht'),
            'birth_year': _('Geburtsjahr'),
        }
        
        help_texts = {
            'username': _("15 Zeichen oder weniger!")
        }
        

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError(_('Passwörter stimmen nicht überein!'))
        return cd['password2']
        
    def clean_username(self):
        cd = self.cleaned_data
        if len(cd['username']) > 15:
            raise forms.ValidationError(_('Nutzername zu lang (max. 15 Zeichen)'))
        return cd['username']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'username', 'sex', 'birth_year', 'profile_text', 'image')

        labels = {
            'sex': _('Geschlecht'),
            'birth_year': _('Geburtsjahr'),
            'profile_text': _('Profiltext'),
            'image': _('Profilbild')
        }
        
        help_texts = {
            'email': _('Falls Sie mal das Passwort zurücksetzen müssen. Optional.'),
            'sex': _('Für Bewerbungen.'),
            'birth_year': _('Altersermittlung für Bewerbungen.')
        }


class LocationForm(forms.Form):
    # , help_text=_('Notwendig, um in Ihrer Nähe nach Leuten suchen zu können. Nur für Ihre Freunde sichtbar.')
    address = forms.CharField(label=_('Ihre Stadt'))

    def clean(self):
        cd = super().clean()
        _ = get_location(cd['address'])
        return cd


class FriendRequestForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, label=_('Nachricht'))

    def clean(self):
        cleaned_data = super().clean()
        message = cleaned_data.get('message')
        if len(message) > 150:
            raise forms.ValidationError(_('Die Nachricht darf nicht länger als 150 Zeichen sein, ist aber {l} Zeichen lang.').format(l=len(message)))
        return cleaned_data


class CustomFriendRequestForm(FriendRequestForm):
    username = forms.CharField(label=_('Nutzername'))

    def clean(self):
        cd = super().clean()
        if not User.objects.filter(username=cd['username']).exists():
            raise forms.ValidationError(_('Es gibt keinen Nutzer mit dem Nutzernamen {name}').format(name=cd["username"]))
        return cd
        
class AccountDeleteForm(forms.Form):
    okay = forms.BooleanField(label=_('Wirklich löschen?'))
    
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('okay'):
            raise forms.ValidationError(_('Bitte bestätigen Sie, dass Sie Ihren Account löschen wollen.'))
        return cleaned_data
    