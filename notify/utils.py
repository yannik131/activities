from .models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from collections.abc import Iterable


def _notify(recipient, actor, action, action_object=None):
    notification = Notification.objects.create(recipient=recipient, actor=actor, action=action, action_object=action_object)
    channel_name = recipient.channel_name
    if channel_name:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(
            channel_name,
            {
                'type': 'notify.notification',
                'text': str(notification)
            }
        )


def notify(recipient, actor, action, action_object=None):
    if isinstance(recipient, Iterable):
        for r in recipient:
            _notify(r, actor, action, action_object)
    else:
        _notify(recipient, actor, action, action_object)
