from time import perf_counter_ns
from django import forms
from .models import Post, Comment
from activity.models import Activity, Category
from usergroups.models import UserGroup
from shared.shared import log, one_or_none, type_of
from django.utils.translation import gettext_lazy as _

class PostForm(forms.ModelForm):
    def __init__(self, arg, language_code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.language_code = language_code
        if type(arg) == UserGroup:
            group = arg
            self.instance.category = group.category
            self.instance.group = group
            self.fields['category'].required = False
            self.fields['category'].disabled = True
            self.fields['category'].initial = group.category.id
            self.fields['activity'].choices = [(None, '-'*10)] + [(activity.id, activity) for activity in self.instance.category.activities.translated(self.language_code).order_by('translations__name')]
        elif type(arg) == Category:
            category = arg
            self.fields['category'].initial = category.id
            self.fields['category'].disabled = True
            self.fields['activity'].choices = [(None, '-'*10)] + [(activity.id, activity) for activity in category.activities.translated(self.language_code).order_by('translations__name')]
        elif type(arg) == Activity:
            activity = arg
            self.fields['category'].disabled = True
            self.fields['category'].initial = activity.categories.first()
            self.fields['activity'].disabled = True
            self.fields['activity'].initial = activity.id
        else:
            self.fields['category'].choices = [(None, '-'*10)] + [(category.id, category) for category in Category.objects.translated(self.language_code).filter(visible=True).order_by('translations__name')]
            self.fields['category'].required = False
            self.fields['activity'].required = False
            self.fields['activity'].choices = [(None, '-'*10)] + [(activity.id, activity) for activity in Activity.objects.translated(self.language_code).order_by('translations__name')]
            

    MAX_UPLOAD_FILE_SIZE = 30000000
    MAX_UPLOAD_FILE_SIZE_STR = str(int(MAX_UPLOAD_FILE_SIZE/1000000)) + "MB"

    class Meta:
        model = Post
        fields = ('message', 'category', 'activity',  'audio', 'video', 'image')

        labels = {
            'message': _('Nachricht'),
            'category': _('Kategorie (erforderlich)'),
            'activity': _('Aktivität (Namen eintippen geht schneller als klicken!)'),
            'audio': _('Audiodatei'),
            'video': _('Videodatei'),
            'image': _('Bilddatei')
        }
        
        help_texts = {
            'message': _('<a target="_blank" href="https://www.heise.de/mac-and-i/downloads/65/1/1/6/7/1/0/3/Markdown-CheatSheet-Deutsch.pdf">[Zum Markdown Merkblatt]</a>')
        }

    def clean_media_fields(self, cd):
        audio = cd.get('audio')
        video = cd.get('video')
        image = cd.get('image')
        if not one_or_none(audio, video, image):
            raise forms.ValidationError(_('Es kann nicht mehr als eine Datei hochgeladen werden.'))
        if audio:
            size = audio.size
            content_type = type_of(audio)
            if not content_type.startswith('audio'):
                raise forms.ValidationError(_('Unbekannter Audiodateityp'))
        elif video:
            size = video.size
            content_type = type_of(video)
            if not content_type.startswith('video'):
                raise forms.ValidationError(_('Unbekannter Videodateityp'))
        elif image:
            size = image.size
            content_type = type_of(image)
            if not content_type.startswith('image'):
                raise forms.ValidationError(_('Unbekannter Bilddateityp'))
        else:
            return
        if size > PostForm.MAX_UPLOAD_FILE_SIZE:
            raise forms.ValidationError(
                _('Maximale Dateigröße: {size1} (tatsächliche Größe: {size2}MB)').format(size1=PostForm.MAX_UPLOAD_FILE_SIZE_STR, size2=round(size / 1000000, 2)))
        self.instance.media_mime_type = content_type

    def clean(self):
        cd = super().clean()
        self.clean_media_fields(cd)
        category = cd.get('category')
        activity = cd.get('activity')
        if category and activity and not self.fields['category'].disabled:
            activity = Activity.objects.get(translations__language_code=self.language_code, translations__name=activity)
            category = Category.objects.get(translations__language_code=self.language_code, translations__name=category)

            if activity not in category.activities.all():
                raise forms.ValidationError(_('Diese Aktivität ist nicht Teil der ausgewählten Kategorie.'))
        elif activity and not category:
            activity = Activity.objects.get(translations__language_code=self.language_code, translations__name=activity)
            cd['category'] = activity.categories.first()
        elif not activity and not category:
            raise forms.ValidationError(_('Es muss entweder eine Kategorie oder eine Aktivität angegeben werden.'))
        return cd


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('message',)

        labels = {
            'message': _('Kommentar')
        }
