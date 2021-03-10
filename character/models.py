from django.db import models
from django.contrib.postgres.fields.hstore import HStoreField
from django.utils.translation import gettext_lazy as _
from activity.models import Activity
from django.urls import reverse

class Character(models.Model):
    TRAITS = {
        'docile': _('gutmütig'),
        'hardy': _('kühn'), 'careful': _('vorsichtig'),
        'jolly': _('froh'), 'melancholic': _('melancholisch'),
        'impish': _('schelmisch'), 'serious': _('ernst'),
        'quirky': _('schrullig'), 'ordinary': _('unauffällig'),
        'relaxed': _('entspannt'), 'impulsive': _('impulsiv'),
        'brave': _('mutig'), 'anxious': _('ängstlich'),
        'solitary': _('einzelgängerisch'), 'social': _('gesellig'),
        'naive': _('naiv'), 'sceptical': _('skeptisch'),
        'sassy': _('frech'), 'polite': _('höflich'),
        'hasty': _('ungestüm'), 'rational': _('überlegt'),
        'calm': _('ruhig'), 'restless': _('rastlos'),
        'sly': _('gewieft'), 'honest': _('ehrlich'),
        'exuberant': _('ausgelassen'), 'timid': _('schüchtern'),
        'modest': _('bescheiden'), 'demanding': _('anspruchsvoll'),
        'inquisitive': _('wissbegierig'), 'idle': _('müßig'),
        'patient': _('geduldig'), 'empathic': _('empathisch')
    }
    values = HStoreField(default=dict, blank=True)
    current_question = models.PositiveSmallIntegerField(default=1)
    suggestions = models.ManyToManyField(Activity, related_name='suggested_to')

    def get_absolute_url(self):
        return reverse('character:overview', args=[])
    
