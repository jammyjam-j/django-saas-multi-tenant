__version__ = "0.1.0"

from .settings import Settings as SaasSettings
from .urls import urlpatterns as saas_urlpatterns
from .wsgi import get_wsgi_application
from .asgi import get_asgi_application

def get_settings():
    return SaasSettings()

def run_wsgi():
    application = get_wsgi_application()
    return application

def run_asgi():
    application = get_asgi_application()
    return application

__all__ = [
    "__version__",
    "SaasSettings",
    "saas_urlpatterns",
    "get_settings",
    "run_wsgi",
    "run_asgi",
]