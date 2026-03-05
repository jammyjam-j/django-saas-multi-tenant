import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.urls import reverse


class TenantQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    domain_url = models.URLField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = "tenant"
        verbose_name_plural = "tenants"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.slug:
            self.slug = slugify(self.name)
        if Tenant.objects.exclude(pk=self.pk).filter(slug=self.slug).exists():
            raise ValidationError({"slug": "Slug must be unique."})
        if Tenant.objects.exclude(pk=self.pk).filter(domain_url=self.domain_url).exists():
            raise ValidationError({"domain_url": "Domain URL must be unique."})

    def get_absolute_url(self):
        return reverse("tenant-detail", kwargs={"pk": self.pk})