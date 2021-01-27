from .models import UserGroup
from django import forms
from account.models import User
from django.utils.translation import gettext as _


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
            admin = cd.get('admin')
            if not admin:
                raise forms.ValidationError(_('Sie müssen einen Administrator auswählen.'))
            elif not self.instance.members.filter(username=admin).exists():
                raise forms.ValidationError(admin+": "+_("Der Macker ist nicht mal in der Gruppe."))
            self.instance.admin = User.objects.get(username=admin)
        return cd
