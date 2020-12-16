import json
from account.models import User
from channels.generic.websocket import WebsocketConsumer


class NotificationConsumer(WebsocketConsumer):

    def connect(self):
        user_id = int(self.scope['url_route']['kwargs']['user_id'])
        self.user = User.objects.get(id=user_id)
        self.user.channel_name = self.channel_name
        self.user.save()
        self.accept()

    def disconnect(self, code):
        self.user.channel_name = None
        self.user.save()

    def receive(self, text_data=None, bytes_data=None):
        pass

    def notify_notification(self, event):
        message = event['text']

        self.send(text_data=json.dumps(dict(message=message)))
