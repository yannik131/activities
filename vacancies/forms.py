from django import forms
from .models import Vacancy, Application, Invitation
from account.models import User
from usergroups.models import UserGroup
from competitions.models import Match, Tournament, Opponent
from django.contrib.contenttypes.models import ContentType


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ('description', 'sex', 'min_age', 'max_age', 'location_component')
        labels = {
            'description': 'Beschreibung',
            'sex': 'Geschlecht',
            'min_age': 'Mindestalter',
            'max_age': 'Höchstalter',
            'location_component': 'Beschränken auf'
        }

    def clean(self):
        cd = super().clean()
        min_age = cd.get('min_age')
        max_age = cd.get('max_age')
        if min_age and max_age:
            if int(min_age) > int(max_age):
                raise forms.ValidationError('Das Mindestalter muss unter dem Höchstalter liegen.')
        component = cd['location_component']
        component_value = self.instance.group.admin.location.get_component(component)
        if component_value is None:
            raise forms.ValidationError('Sie wohnen in einer kreisfreien Stadt. Bitte wählen Sie eine andere Komponente aus.')
        self.instance.location_component_value = component_value
        return cd


class InvitationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invite_group = kwargs.get('invite_group', False)
        if self.invite_group:
            self.fields['user'].disabled = True
            self.fields['user'].required = False
        else:
            self.fields['group'].disabled = True
            self.fields['group'].required = False

    user = forms.CharField(label='Nutzername')
    group = forms.CharField(label='Gruppenname')

    class Meta:
        model = Invitation
        fields = ('message',)
        labels = {
            'message': 'Nachricht'
        }
        widgets = {
            'message': forms.Textarea()
        }

    def clean(self):
        # self.instance.sender is set from within the respective view function
        # ATTENTION: The sender is used in this function and needs to be set BEFORE save/clean are called!
        cd = super().clean()
        if self.invite_group:
            try:
                group = UserGroup.objects.get(name=cd['group'])
            except UserGroup.DoesNotExist:
                raise forms.ValidationError(f"Keine Gruppe mit dem Namen {cd['group']} gefunden.")
        else:
            try:
                user = User.objects.get(name=cd['user'])
            except User.DoesNotExist:
                raise forms.ValidationError(f"Keinen Nutzer mit dem Nutzernamen {cd['user']} gefunden.")
        instance = self.instance
        if self.invite_group:
            target_ct = UserGroup.content_type()
            target_id = group.id
        else:
            target_ct = User.content_type()
            target_id = user.id
        if Invitation.objects.filter(sender_ct=instance.sender_ct, sender_id=instance.sender_id,
                                     target_ct=target_ct, target_id=target_id).exists():
            raise forms.ValidationError("Dieser Nutzer bzw. diese Gruppe wurde bereits eingeladen und hat entweder"\
                                        " abgelehnt oder noch nicht zugesagt.")
        if Opponent.objects.filter(instance_ct=target_ct, instance_id=target_id,
                                   target_ct=instance.sender_ct, target_id=instance.sender_id).exists():
            raise forms.ValidationError("Dieser Nutzer bzw. diese Gruppe befindet sich bereits in diesem Match bzw."\
                                        " diesem Turnier.")
        elif not self.invite_group:
            group = instance.sender_ct.get_objects_for_this_type(id=instance.sender_id)
            if user in group.members.all():
                raise forms.ValidationError("Dieser Nutzer befindet sich bereits in der Gruppe.")
        return cd


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('message',)
        labels = {
            'message': 'Nachricht'
        }
        widgets = {
            'message': forms.Textarea()
        }
