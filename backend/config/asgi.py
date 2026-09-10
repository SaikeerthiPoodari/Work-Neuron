import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

django.setup()

from apps.notifications.middleware import JWTAuthMiddleware
from config.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
