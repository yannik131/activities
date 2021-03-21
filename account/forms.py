from django import forms
from django.contrib.auth import get_user_model
from account.models import User
from .utils import get_location
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from datetime import datetime


class UserRegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        
    password = forms.CharField(label=_('Passwort'),
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Passwort (erneut)'),
                                widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('email', 'username')
        labels = {
            'sex': _('Geschlecht'),
            'birth_year': _('Geburtsjahr'),
            'email': _('E-Mail Adresse')
        }
        
        help_texts = {
            'username': "",
        }
        
    def clean_username(self):
        username = self.cleaned_data['username']
        try: 
            validate_email(username)
            
        except ValidationError:
            return username
        raise forms.ValidationError(_('Ihr Nutzername kann keine E-Mail sein. Das wäre verwirrend, oder?'))
        
    def clean_email(self):
        cd = self.cleaned_data
        if User.objects.filter(email=cd['email']).exists():
            raise forms.ValidationError(_('Es gibt schon einen Nutzer mit dieser E-Mail-Adresse.'))
        return cd['email']
    
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError(_('Passwörter stimmen nicht überein!'))
        return cd['password2']
        
    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) > 15:
            raise forms.ValidationError(_('Nutzername zu lang (max. 15 Zeichen)'))
        try: 
            validate_email(username)
        except ValidationError:
            return username
        raise forms.ValidationError(_('Ihr Nutzername kann keine E-Mail sein. Das wäre verwirrend, oder?'))


class UserEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
    
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
            'email': _('Für Login und Passwort-Zurücksetzen.'),
            'sex': _('Für Bewerbungen.'),
            'birth_year': _('Altersermittlung für Bewerbungen.'),
            'username': ''
        }
        
    def clean_birth_year(self):
        birth_year = int(self.cleaned_data['birth_year'])
        year = datetime.today().year
        if birth_year > (year-3):
            raise forms.ValidationError(_('Sie müssen mindestens 3 Jahre alt sein, um diese Seite überhaupt nutzen zu können. Jüngere Menschen haben noch kein Gedächtnis.'))
        elif year-birth_year > 120:
            raise forms.ValidationError(_('Es ist statistisch doch sehr unwahrscheinlich, dass Sie älter als 120 sind.'))
        return birth_year
        
    


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
    

def authenticate(user_input, password):
    try:
        user = User.objects.get(username=user_input)
    except User.DoesNotExist:
        try:
            user = User.objects.get(email=user_input)
        except User.DoesNotExist:
            return None
    if check_password(password, user.password):
        return user
    return False

class LoginForm(forms.Form):
    user_input = forms.CharField(max_length=25, label=_('E-Mail oder Nutzername'))
    password = forms.CharField(max_length=100, label=_('Passwort'), widget=forms.PasswordInput())
    
    def clean(self):
        cd = super().clean()
        self.user = authenticate(cd['user_input'], cd['password'])
        if self.user is None:
            raise forms.ValidationError(_('Nutzer nicht gefunden.'))
        elif self.user is False:
            raise forms.ValidationError(_('Passwort falsch.'))
        elif self.user.is_active is False:
            raise forms.ValidationError(_('Der Account wurde noch nicht aktiviert! Checken Sie Ihre Mails.'))
        return cd
    