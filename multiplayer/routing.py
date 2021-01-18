from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/multiplayer/durak/(?P<match_id>\d+)/(?P<username>\w+)/$', consumers.DurakConsumer),
    re_path(r'ws/multiplayer/skat/(?P<match_id>\d+)/(?P<username>\w+)/$', consumers.SkatConsumer)
]