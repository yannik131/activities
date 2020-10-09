from django import forms
from .models import Post, Comment
from activity.models import Activity, Category
from shared.shared import xor_or_none, type_of


class PostForm(forms.ModelForm):
    def __init__(self, group, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if group:
            self.instance.category = group.category
            self.instance.group = group
            self.fields['category'].required = False
            self.fields['category'].disabled = True
            self.fields['category'].initial = group.category.id
            self.fields['activity'].choices = [(None, '-'*10)] + [(activity.id, activity) for activity in self.instance.category.activities.all()]

    MAX_UPLOAD_FILE_SIZE = 30000000
    MAX_UPLOAD_FILE_SIZE_STR = str(int(MAX_UPLOAD_FILE_SIZE/1000000)) + "MB"

    class Meta:
        model = Post
        fields = ('message', 'category', 'activity',  'audio', 'video', 'image')

        labels = {
            'message': 'Nachricht',
            'category': 'Kategorie (erforderlich)',
            'activity': 'Aktivität',
            'audio': 'Audiodatei',
            'video': 'Videodatei',
            'image': 'Bilddatei'
        }

        help_texts = {
            'message': '<..>: Link, *..*: Kursiv, **..**: Fett, ***..***: Kursiv+Fett, * ..: Liste, 1. ..; 2 ..: Liste mit Zahlen'
        }

    def clean_media_fields(self, cd):
        audio = cd.get('audio')
        video = cd.get('video')
        image = cd.get('image')
        if not xor_or_none(audio, video, image):
            raise forms.ValidationError('Es kann nicht mehr als eine Datei hochgeladen werden.')
        if audio:
            size = audio.size
            content_type = type_of(audio)
            if not content_type.startswith('audio'):
                raise forms.ValidationError('Unbekannter Audiodateityp')
        elif video:
            size = video.size
            content_type = type_of(video)
            if not content_type.startswith('video'):
                raise forms.ValidationError('Unbekannter Videodateityp')
        elif image:
            size = image.size
            content_type = type_of(image)
            if not content_type.startswith('image'):
                raise forms.ValidationError('Unbekannter Bilddateityp')
        else:
            return
        if size > PostForm.MAX_UPLOAD_FILE_SIZE:
            raise forms.ValidationError(
                f'Maximale Dateigröße: {PostForm.MAX_UPLOAD_FILE_SIZE_STR} (tatsächliche Größe: {round(size / 1000000, 2)}MB)')
        self.instance.media_mime_type = content_type

    def clean(self):
        cd = super().clean()
        self.clean_media_fields(cd)
        category = cd.get('category')
        activity = cd.get('activity')
        if category and activity:
            activity = Activity.objects.get(name=activity)
            category = Category.objects.get(name=category)
            if activity not in category.activities.all():
                raise forms.ValidationError('Diese Aktivität ist nicht Teil der ausgewählten Kategorie.')
        return cd


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('message',)

        labels = {
            'message': 'Kommentar'
        }
