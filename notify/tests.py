from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from account.models import User

layer = get_channel_layer()
u = User.objects.get(username='test')
async_to_sync(layer.send)(u.channel_name, dict(type='notify.notification', text='hi'))
