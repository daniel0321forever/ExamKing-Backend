"""
ASGI config for testing_game project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import URLRouter, ProtocolTypeRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testing_game.settings")
http_application = get_asgi_application()

from gaming.middleware import FieldValidateMiddleware
import gaming.routing

application = ProtocolTypeRouter({
    'http': http_application,
    'websocket': FieldValidateMiddleware(
        AuthMiddlewareStack(
            URLRouter(gaming.routing.websocket_urlpatterns)
        )
    )
})