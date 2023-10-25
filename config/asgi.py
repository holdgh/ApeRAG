"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path, re_path

from kubechat.chat.routing import websocket_urlpatterns
from kubechat.chat.sse import ServerSentEventsConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from kubechat.auth.validator import WebSocketAuthMiddleware, HTTPAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": URLRouter([
            path('events', ServerSentEventsConsumer.as_asgi()),
            re_path(r'', get_asgi_application()),
        ]),
        "websocket": WebSocketAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
