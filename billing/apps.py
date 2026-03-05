from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class BillingConfig(AppConfig):
    name = "billing"
    verbose_name = "Billing Module"

    def ready(self) -> None:
        try:
            from .signals import register_payment_webhook
            register_payment_webhook()
            logger.info("Payment webhook registered successfully.")
        except Exception as exc:
            logger.exception("Failed to register payment webhook: %s", exc)
        try:
            from .tasks import schedule_due_date_checks
            schedule_due_date_checks()
            logger.info("Due date check task scheduled.")
        except Exception as exc:
            logger.exception("Failed to schedule due date checks: %s", exc)