from django import forms
from .models import Vacancy, Application, Invitation
from account.models import User
from usergroups.models import UserGroup
from django.utils.translation import gettext_lazy as _


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ('description', 'sex', 'min_age', 'max_age', 'location_component', 'persistent')
        labels = {
            'description': _('Beschreibung'),
            'sex': _('Geschlecht'),
            'min_age': _('Mindestalter'),
            'max_age': _('Höchstalter'),
            'location_component': _('Beschränken auf'),
            'persistent': _('Leerstelle nach Annahme einer Bewerbung nicht löschen')
        }

    def clean(self):
        cd = super().clean()
        min_age = cd.get('min_age')
        max_age = cd.get('max_age')
        if min_age and max_age:
            if int(min_age) > int(max_age):
                raise forms.ValidationError(_('Das Mindestalter muss unter dem Höchstalter liegen.'))
        component = cd['location_component']
        component_value = getattr(self.instance.target.admin.location, component)
        if component_value is None:
            raise forms.ValidationError(_('Sie wohnen in einer kreisfreien Stadt. Bitte wählen Sie eine andere Komponente aus.'))
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
            pass
            #self.fields['group'].disabled = True
            #self.fields['group'].required = False

    user = forms.CharField(label='Nutzername')
    #group = forms.CharField(label='Gruppenname')

    class Meta:
        model = Invitation
        fields = ('message',)
        labels = {
            'message': _('Nachricht')
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
                raise forms.ValidationError(_("Keine Gruppe mit dem Namen {name} gefunden.").format(name=cd['group']))
        else:
            try:
                user = User.objects.get(username=cd['user'])
            except User.DoesNotExist:
                raise forms.ValidationError(_("Keinen Nutzer mit dem Nutzernamen {name} gefunden.").format(name=cd['user']))
        instance = self.instance
        if self.invite_group:
            target_ct = UserGroup.content_type()
            target_id = group.id
        else:
            target_ct = User.content_type()
            target_id = user.id
        if Invitation.objects.filter(sender_ct=instance.sender_ct, sender_id=instance.sender_id, target_ct=target_ct, target_id=target_id).exists():
            raise forms.ValidationError(_("Dieser Nutzer bzw. diese Gruppe wurde bereits eingeladen und hat entweder abgelehnt oder noch nicht zugesagt."))
        if self.invite_group and group in self.instance.sender.groups.all() or\
            not self.invite_group and user in self.instance.sender.members.all():
            raise forms.ValidationError(_("Dieser Nutzer bzw. diese Gruppe ist bereits Mitglied."))
        if self.invite_group:
            self.instance.target = group
        else:
            self.instance.target = user
        return cd


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('message',)
        labels = {
            'message': _('Nachricht')
        }
        widgets = {
            'message': forms.Textarea()
        }
