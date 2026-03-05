from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, RegexValidator
from tenants.models import Tenant


class Plan(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    monthly_rate_cents = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    max_users = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-monthly_rate_cents"]


class Subscription(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def cancel(self):
        self.end_date = timezone.now().date()
        self.active = False
        self.save(update_fields=["end_date", "active"])

    def renew(self):
        if not self.active:
            self.start_date = timezone.now().date()
            self.end_date = None
            self.active = True
            self.save(update_fields=["start_date", "end_date", "active"])

    @property
    def next_billing_date(self):
        if self.end_date:
            return None
        return self.start_date + timezone.timedelta(days=30)

    class Meta:
        ordering = ["-start_date"]


class Invoice(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="invoices")
    period_start = models.DateField()
    period_end = models.DateField()
    amount_cents = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_paid(self):
        self.paid = True
        self.save(update_fields=["paid"])

    @property
    def formatted_amount(self):
        return f"${self.amount_cents / 100:.2f}"

    class Meta:
        ordering = ["-period_start"]


class Usage(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="usages")
    metric = models.CharField(max_length=64)
    value = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("tenant", "metric", "recorded_at")
        ordering = ["-recorded_at"]


class UsageThreshold(models.Model):
    metric = models.CharField(max_length=64, unique=True)
    threshold_cents = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    notification_email = models.EmailField()

    def __str__(self):
        return f"{self.metric} ({self.threshold_cents} cents)"


class BillingEvent(models.Model):
    EVENT_CHOICES = [
        ("invoice_created", "Invoice Created"),
        ("payment_received", "Payment Received"),
        ("usage_exceeded", "Usage Exceeded"),
    ]
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    payload = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]


class CreditCard(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="credit_card")
    card_number = models.CharField(
        max_length=19,
        validators=[RegexValidator(r"^\d{13,19}$", message="Invalid card number")],
    )
    exp_month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), RegexValidator(r"^(0[1-9]|1[0-2])$", message="Invalid month")])
    exp_year = models.PositiveSmallIntegerField()
    cvc = models.CharField(max_length=4, validators=[RegexValidator(r"^\d{3,4}$", message="Invalid CVC")])

    def is_valid(self):
        if self.exp_year < timezone.now().year:
            return False
        if self.exp_year == timezone.now().year and self.exp_month < timezone.now().month:
            return False
        return True

    def __str__(self):
        return f"{self.card_number[-4:]} (exp {self.exp_month}/{self.exp_year})"