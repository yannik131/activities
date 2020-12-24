from .models import UserGroup
from django import forms
from account.models import User
from django.utils.translation import gettext_lazy as _


class GroupForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edit_mode = 'instance' in kwargs
        self.fields['admin'].disabled = not self.edit_mode
        self.fields['admin'].required = self.edit_mode

    admin = forms.CharField(label=_('Administrator (Nutzername)'), disabled=True)

    class Meta:
        model = UserGroup
        fields = ('name', 'description', 'public', 'image')
        labels = {
            'name': _('Name'),
            'description': _('Beschreibung'),
            'public': _('Öffentlich'),
            'image': _('Gruppenbild')
        }

        widgets = {
            'description': forms.Textarea()
        }

    def clean(self):
        cd = super(GroupForm, self).clean()
        name, description = cd['name'], cd['description']
        if len(name) > 30 or description and len(description) > 150:
            raise forms.ValidationError(_('Der Name darf nicht länger als 30, die Beschreibung nicht länger als 150 Zeichen lang sein.'))
        if self.edit_mode:
            if self.instance.admin and not cd.get('admin'):
                raise forms.ValidationError(_('Sie müssen einen Administrator auswählen.'))
            try:
                self.instance.set_admin(User.objects.get(username=cd['admin']))
            except User.DoesNotExist:
                raise forms.ValidationError(_("Keinen Nutzer mit dem Nutzernamen {name} gefunden.").format(name=cd['admin']))
        return cd
