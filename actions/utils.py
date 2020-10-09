from django.contrib.contenttypes.models import ContentType
from .models import Action
from django.utils import timezone
import datetime
from django.db.models import Q


def create_action(source, verb, target=None):
    now = timezone.now()
    last_minute = now - datetime.timedelta(seconds=60)
    source_ct = ContentType.objects.get_for_model(source)
    similar_actions = Action.objects.filter(
        source_id=source.id, source_ct=source_ct, verb=verb, created__gte=last_minute)
    if target:
        target_ct = ContentType.objects.get_for_model(target)
        similar_actions = similar_actions.filter(target_ct=target_ct, target_id=target.id)
    if not similar_actions:
        action = Action(source=source, verb=verb, target=target)
        action.save()
        return True
    return False
