from django.urls import path

from .consumers import WSConsumer

ws_urlpatterns = [
    path('ws/completions/', WSConsumer.as_asgi())
]