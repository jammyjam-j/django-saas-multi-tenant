from django.contrib import admin
from django.utils.html import format_html

from .models import Invoice, Subscription, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tenant',
        'amount',
        'status',
        'created_at',
        'due_date',
        'actions',
    )
    list_filter = ('status', 'tenant')
    search_fields = ('tenant__name', 'invoice_number')
    readonly_fields = (
        'invoice_number',
        'created_at',
        'updated_at',
        'generated_by',
        'pdf_url',
    )
    fieldsets = (
        (None, {
            'fields': (
                'tenant',
                'invoice_number',
                'amount',
                'status',
                'due_date',
                'notes',
            ),
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
                'generated_by',
                'pdf_url',
            ),
        }),
    )
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(
            request,
            f'{updated} invoice(s) marked as paid.'
        )

    mark_as_paid.short_description = 'Mark selected invoices as paid'

    def pdf_url(self, obj):
        if not obj.pdf_file:
            return '-'
        url = obj.pdf_file.url
        return format_html('<a href="{}" target="_blank">View PDF</a>', url)

    pdf_url.short_description = 'PDF'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tenant',
        'plan_name',
        'start_date',
        'end_date',
        'status',
        'actions',
    )
    list_filter = ('status', 'plan_name')
    search_fields = ('tenant__name', 'plan_name')
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (None, {
            'fields': (
                'tenant',
                'plan_name',
                'amount',
                'status',
                'start_date',
                'end_date',
                'notes',
            ),
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    actions = ['cancel_selected']

    def cancel_selected(self, request, queryset):
        updated = queryset.update(status='canceled')
        self.message_user(
            request,
            f'{updated} subscription(s) canceled.'
        )

    cancel_selected.short_description = 'Cancel selected subscriptions'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'invoice',
        'amount_paid',
        'payment_date',
        'status',
        'transaction_id',
        'actions',
    )
    list_filter = ('status', 'payment_date')
    search_fields = ('invoice__invoice_number', 'transaction_id')
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (None, {
            'fields': (
                'invoice',
                'amount_paid',
                'status',
                'payment_date',
                'transaction_id',
                'notes',
            ),
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    actions = ['mark_as_successful']

    def mark_as_successful(self, request, queryset):
        updated = queryset.update(status='successful')
        self.message_user(
            request,
            f'{updated} payment(s) marked as successful.'
        )

    mark_as_successful.short_description = 'Mark selected payments as successful'