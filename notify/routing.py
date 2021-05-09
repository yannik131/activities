from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/user/(?P<user_id>\d+)/(?P<key>-?\d+)/$', consumers.NotificationConsumer.as_asgi())
]