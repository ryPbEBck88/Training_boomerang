"""
ASGI config for training project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'training.settings')

django_asgi = get_asgi_application()

from pvp import routing as pvp_routing

application = ProtocolTypeRouter({
    'http': django_asgi,
    'websocket': AuthMiddlewareStack(
        URLRouter(pvp_routing.websocket_urlpatterns)
    ),
})
