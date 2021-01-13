from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import notify.routing
import durak.routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            notify.routing.websocket_urlpatterns +
            durak.routing.websocket_urlpatterns
        )
    ),
})