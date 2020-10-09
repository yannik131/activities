from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/room/(?P<app_label>[^/]+)/(?P<model>[^/]+)/(?P<id>\d+)/$', consumers.ChatConsumer),
]