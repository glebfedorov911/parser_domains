"""
ASGI config for siteparsershops project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django

from django.core.asgi import get_asgi_application
from django.urls import path
from django.conf import settings

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from parser.consumers import MyWSConsumer

# os.environ['DJANGO_SETTINGS_MODULE']='siteparsershops.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'siteparsershops.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/parser/", MyWSConsumer.as_asgi()),
        ])
    ),
})
