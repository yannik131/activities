from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/multiplayer/durak/(?P<match_id>\d+)/(?P<username>\w+)/$', consumers.DurakConsumer.as_asgi()),
    re_path(r'ws/multiplayer/skat/(?P<match_id>\d+)/(?P<username>\w+)/$', consumers.SkatConsumer.as_asgi()),
    re_path(r'ws/multiplayer/doppelkopf/(?P<match_id>\d+)/(?P<username>\w+)/$', consumers.DoppelkopfConsumer.as_asgi())
]