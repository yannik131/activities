from django import forms
from django.contrib.auth import get_user_model
from account.models import User
from shared import shared


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Passwort',
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label='Passwort (erneut)',
                                widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'email', 'sex', 'birth_year')
        labels = {
            'sex': 'Geschlecht',
            'birth_year': 'Geburtsjahr',
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwörter stimmen nicht überein!')
        return cd['password2']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'username', 'sex', 'birth_year', 'profile_text')

        labels = {
            'sex': 'Geschlecht',
            'birth_year': 'Geburtsjahr',
            'profile_text': 'Profiltext'
        }


class LocationForm(forms.Form):
    address = forms.CharField(label='Adresse')


class FriendRequestForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, label='Nachricht')

    def clean(self):
        cleaned_data = super().clean()
        message = cleaned_data.get('message')
        if len(message) > 150:
            raise forms.ValidationError('Die Nachricht darf nicht länger als 150 Zeichen sein, ist aber ' + str(len(message)) + ' Zeichen lang.')
        return cleaned_data


class CustomFriendRequestForm(FriendRequestForm):
    username = forms.CharField(label='Nutzername')

    def clean(self):
        cd = super().clean()
        if not User.objects.filter(username=cd['username']).exists():
            raise forms.ValidationError(f'Es gibt keinen Nutzer mit dem Nutzernamen {cd["username"]}')
        return cd
