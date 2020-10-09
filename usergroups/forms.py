from .models import UserGroup
from django import forms
from account.models import User


class GroupForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edit_mode = 'instance' in kwargs
        self.fields['admin'].disabled = not self.edit_mode
        self.fields['admin'].required = self.edit_mode

    admin = forms.CharField(label='Administrator (Nutzername)', disabled=True)

    class Meta:
        model = UserGroup
        fields = ('name', 'description', 'public')
        labels = {
            'name': 'Name',
            'description': 'Beschreibung',
            'public': 'Öffentlich'
        }

        widgets = {
            'description': forms.Textarea()
        }

    def clean(self):
        cd = super(GroupForm, self).clean()
        name, description = cd['name'], cd['description']
        if len(name) > 30 or description and len(description) > 150:
            raise forms.ValidationError('Der Name darf nicht länger als 30, die Beschreibung nicht länger als 150 Zeichen lang sein.')
        if self.edit_mode:
            if self.instance.admin and not cd.get('admin'):
                raise forms.ValidationError('Sie müssen einen Administrator auswählen.')
            try:
                self.instance.set_admin(User.objects.get(username=cd['admin']))
            except User.DoesNotExist:
                raise forms.ValidationError(f"Keinen Nutzer mit dem Nutzernamen {cd['admin']} gefunden.")
        return cd
