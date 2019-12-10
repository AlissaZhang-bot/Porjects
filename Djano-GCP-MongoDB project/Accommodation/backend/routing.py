##=====================================================
# Set up websocket url link, transfer asynchronous data
##=====================================================

from django.urls import path
from .consumers import ChatConsumer

### routing the asynchronous path for chatbot
websocket_urlpatterns = [
    path('ws/chat/', ChatConsumer),
]