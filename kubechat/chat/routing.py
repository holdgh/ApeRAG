from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/collections/(?P<collection_id>\w+)/$", consumers.EchoConsumer.as_asgi()),
]