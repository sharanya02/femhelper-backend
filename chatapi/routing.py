from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<token>\w+)/(?P<receiver_id>\d+)/(?P<is_request_acceptor>\d+)/$', consumers.ChatConsumer),
]