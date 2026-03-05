import datetime
import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils.timezone import now

from celery import shared_task

from billing.models import Invoice, Subscription, PaymentMethod
from tenants.models import Tenant

logger = logging.getLogger(__name__)

@shared_task
def generate_monthly_invoices():
    start_of_month = datetime.date(now().year, now().month, 1)
    end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

    active_subscriptions = Subscription.objects.filter(
        is_active=True,
        start_date__lte=end_of_month,
        end_date__gte=start_of_month
    ).select_related('tenant', 'plan')

    for subscription in active_subscriptions:
        try:
            with transaction.atomic():
                amount_due = Decimal(subscription.plan.price)
                invoice, created = Invoice.objects.get_or_create(
                    tenant=subscription.tenant,
                    subscription=subscription,
                    period_start=start_of_month,
                    period_end=end_of_month,
                    defaults={
                        'amount': amount_due,
                        'status': Invoice.Status.PENDING
                    }
                )
                if not created and invoice.status != Invoice.Status.PENDING:
                    continue

                send_invoice_email.delay(invoice.id)
        except Exception as exc:
            logger.exception(f"Failed to generate invoice for subscription {subscription.pk}: {exc}")

@shared_task
def process_payment(invoice_id):
    try:
        invoice = Invoice.objects.select_related('tenant', 'subscription').get(pk=invoice_id)
    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} does not exist")
        return

    if invoice.status != Invoice.Status.PENDING:
        logger.info(f"Invoice {invoice_id} already processed with status {invoice.status}")
        return

    payment_method = PaymentMethod.objects.filter(tenant=invoice.tenant, is_default=True).first()
    if not payment_method:
        logger.error(f"No default payment method for tenant {invoice.tenant.pk}")
        invoice.status = Invoice.Status.FAILED
        invoice.save(update_fields=['status'])
        return

    try:
        with transaction.atomic():
            # Simulate payment gateway interaction
            success = mock_payment_gateway(payment_method, invoice.amount)
            if success:
                PaymentMethod.objects.create(
                    tenant=invoice.tenant,
                    reference_id=f"PAY-{invoice.id}-{now().strftime('%Y%m%d%H%M%S')}",
                    amount_paid=invoice.amount,
                    status=PaymentMethod.Status.COMPLETED
                )
                invoice.status = Invoice.Status.PAID
                invoice.paid_at = now()
            else:
                invoice.status = Invoice.Status.FAILED
            invoice.save(update_fields=['status', 'paid_at'])
    except Exception as exc:
        logger.exception(f"Error processing payment for invoice {invoice_id}: {exc}")
        invoice.status = Invoice.Status.FAILED
        invoice.save(update_fields=['status'])

def mock_payment_gateway(payment_method, amount):
    if payment_method.provider == PaymentMethod.Provider.BANK_TRANSFER:
        return True
    if payment_method.provider == PaymentMethod.Provider.CREDIT_CARD:
        return datetime.datetime.now().second % 2 == 0
    return False

@shared_task
def send_invoice_email(invoice_id):
    try:
        invoice = Invoice.objects.select_related('tenant').get(pk=invoice_id)
    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} does not exist for email sending")
        return

    subject = f"Your Invoice #{invoice.id}"
    message = (
        f"Hello {invoice.tenant.name},\n\n"
        f"You have an invoice for the period {invoice.period_start} to {invoice.period_end}.\n"
        f"Amount: ${invoice.amount}\n"
        f"Status: {invoice.get_status_display()}\n\n"
        "Thank you for using our service."
    )
    recipient_list = [invoice.tenant.contact_email]
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False
        )
    except Exception as exc:
        logger.exception(f"Failed to send invoice email for invoice {invoice_id}: {exc}")
```