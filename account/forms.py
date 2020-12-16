from django import forms
from django.contrib.auth import get_user_model
from account.models import User
from shared import shared
from django.utils.translation import gettext_lazy as _


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label=_('Passwort'),
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Passwort (erneut)'),
                                widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'email', 'sex', 'birth_year')
        labels = {
            'sex': _('Geschlecht'),
            'birth_year': _('Geburtsjahr'),
        }
        help_texts = {
            'email': _('Erforderlich für eine Passwort-Zurücksetzung.'),
            'sex': _('Für Bewerbungen.'),
            'birth_year': _('Altersermittlung für Bewerbungen.')
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError(_('Passwörter stimmen nicht überein!'))

        return cd['password2']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'username', 'sex', 'birth_year', 'profile_text')

        labels = {
            'sex': _('Geschlecht'),
            'birth_year': _('Geburtsjahr'),
            'profile_text': _('Profiltext')
        }


class LocationForm(forms.Form):
    address = forms.CharField(label=_('Wohnort'), help_text=_('Notwendig, um in Ihrer Nähe nach Leuten suchen zu können. Nur für Ihre Freunde sichtbar.'))

    def clean(self):
        cd = super().clean()
        _ = shared.get_location(cd['address'])
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
