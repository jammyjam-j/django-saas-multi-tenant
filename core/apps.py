from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        try:
            from . import signals
            logger.info("Core signals module imported successfully.")
        except Exception as exc:
            raise ImproperlyConfigured(f"Failed to import core.signals: {exc}") from exc

        try:
            from .middleware import CoreMiddleware
            if not hasattr(CoreMiddleware, "process_request"):
                raise AttributeError("CoreMiddleware must implement process_request")
            logger.info("Core middleware validated successfully.")
        except Exception as exc:
            raise ImproperlyConfigured(f"Failed to validate core.middleware: {exc}") from exc

        try:
            from .utils import register_util_functions
            register_util_functions()
            logger.info("Utility functions registered successfully.")
        except Exception as exc:
            logger.warning(f"Utility function registration failed: {exc}")

        try:
            from django.conf import settings
            if not hasattr(settings, "CORE_FEATURES"):
                raise AttributeError("Settings must define CORE_FEATURES")
            logger.debug(f"Core features configured: {settings.CORE_FEATURES}")
        except Exception as exc:
            logger.error(f"Core configuration error: {exc}")