import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas.settings')

try:
    application = get_wsgi_application()
except Exception as exc:
    raise RuntimeError(f'Failed to load WSGI application: {exc}') from exc

if not hasattr(application, '__call__'):
    raise TypeError('WSGI application is not callable')