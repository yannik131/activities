from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Action(models.Model):
    """
    TODO: Die Action speichert keinen vollen Satz, sondern nur source, target, time und WAS passiert ist: gelöscht, erstellt, beigetreten, etc. Der Text wird dann der ausgewählten Sprache entsprechend generiert statt gespeichert. Problem: Beinhaltet der Text Datumsangaben müssten diese geparsed und an die entsprechende Sprache angepasst werden. Insbesondere wenn was gelöscht wurde kann man kein Objekt speichern, sondern nur einen Titel etc.
    """
    source_ct = models.ForeignKey(ContentType,
                                  blank=True,
                                  null=True,
                                  related_name='source_obj',
                                  on_delete=models.CASCADE)
    source_id = models.PositiveIntegerField(null=True,
                                            blank=True,
                                            db_index=True)
    source = GenericForeignKey('source_ct', 'source_id')
    verb = models.CharField(max_length=255)
    target_ct = models.ForeignKey(ContentType,
                                  blank=True,
                                  null=True,
                                  related_name='target_obj',
                                  on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True,
                                            blank=True,
                                            db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')
    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    class Meta:
        ordering = ('-created',)