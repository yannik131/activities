from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import notify.routing
import multiplayer.routing
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            notify.routing.websocket_urlpatterns +
            multiplayer.routing.websocket_urlpatterns
        )
    ),
})