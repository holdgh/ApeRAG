from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"api/v1/collections/(?P<collection_id>\w+)/chats/(?P<chat_id>\w+)/connect$",
        consumers.KubeChatEchoConsumer.as_asgi()
    ),
]
