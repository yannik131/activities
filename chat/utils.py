from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from shared.shared import log


channel_layer = get_channel_layer()

def broadcast(users, message):
    for user in users:
        if user.channel_name:
            async_to_sync(channel_layer.send)(
                user.channel_name,
                message
            )