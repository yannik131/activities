from django import forms
from django.contrib.auth import get_user_model
from account.models import User, Location
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from datetime import datetime


class UserForm(forms.ModelForm):
    
    def clean_email(self):
        cd = self.cleaned_data
        query = User.objects.filter(email=cd['email'])
        if query.exists():
            user = query.first()
            if user.is_active:
                raise forms.ValidationError(_('Es gibt schon einen Nutzer mit dieser E-Mail-Adresse.'))
            else:
                user.delete()
        return cd['email']
    
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError(_('Passwörter stimmen nicht überein!'))
        return cd['password2']
        
    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) > 10:
            raise forms.ValidationError(_('Nutzername zu lang (max. 10 Zeichen)'))
        try: 
            validate_email(username)
        except ValidationError:
            return username
        raise forms.ValidationError(_('Ihr Nutzername kann keine E-Mail sein. Das wäre verwirrend, oder?'))
        
    def clean_birth_year(self):
        birth_year = self.cleaned_data['birth_year']
        if birth_year:
            birth_year = int(birth_year)
            year = datetime.today().year
            if birth_year > (year-3):
                raise forms.ValidationError(_('Sie müssen mindestens 3 Jahre alt sein, um diese Seite überhaupt nutzen zu können. Jüngere Menschen haben noch kein Gedächtnis.'))
            elif year-birth_year > 120:
                raise forms.ValidationError(_('Es ist statistisch doch sehr unwahrscheinlich, dass Sie älter als 120 sind.'))
            return birth_year
        else:
            return None

class UserRegistrationForm(UserForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    
        self.fields['email'].required = True
        
    password = forms.CharField(label=_('Passwort'),
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Passwort (erneut)'),
                                widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('email', 'username', 'sex', 'birth_year', 'image')
        labels = {
            'sex': _('Geschlecht (optional)'),
            'birth_year': _('Geburtsjahr (optional)'),
            'email': _('E-Mail Adresse'),
            'image': _('Profilbild (optional): Bitte lächeln!'),
            'username': _('Nutzername (max. 10 Zeichen)')
        }
        
        help_texts = {
            'username': ''
        }
        
class UserEditForm(UserForm):
        
    class Meta:
        model = get_user_model()
        fields = ('sex', 'birth_year', 'profile_text', 'image')
        labels = {
            'sex': _('Geschlecht (freiwillig)'),
            'birth_year': _('Geburtsjahr (freiwillig)'),
            'profile_text': _('Profiltext'),
            'image': _('Profilbild'),
        }

class LocationForm(forms.Form):
    # , help_text=_('Notwendig, um in Ihrer Nähe nach Leuten suchen zu können. Nur für Ihre Freunde sichtbar.')
    address = forms.CharField(label=_('Stadt, Bundesland'))

    def clean(self):
        cd = super().clean()
        self.location = Location.determine_from(cd['address'])
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
        

class DeleteForm(forms.Form):
    okay = forms.BooleanField(label=_('Wirklich löschen?'), required=True)
    

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
    user_input = forms.CharField(max_length=35, label=_('E-Mail oder Nutzername'))
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
    