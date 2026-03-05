from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Subscription, Invoice


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id',
            'user',
            'plan',
            'plan_name',
            'start_date',
            'end_date',
            'status',
        ]
        read_only_fields = ['id', 'user', 'plan_name']

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {'end_date': _('End date must be after start date.')}
            )
        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.all(), source='subscription', write_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            'id',
            'subscription',
            'subscription_id',
            'total_amount',
            'issue_date',
            'due_date',
            'payment_status',
        ]
        read_only_fields = ['id', 'subscription']

    def validate(self, attrs):
        issue_date = attrs.get('issue_date')
        due_date = attrs.get('due_date')
        if issue_date and due_date and due_date < issue_date:
            raise serializers.ValidationError(
                {'due_date': _('Due date must be after issue date.')}
            )
        return attrs

    def create(self, validated_data):
        subscription = validated_data.pop('subscription')
        invoice = Invoice.objects.create(subscription=subscription, **validated_data)
        return invoice


class PaymentSerializer(serializers.Serializer):
    invoice_id = serializers.PrimaryKeyRelatedField(
        queryset=Invoice.objects.all(), source='invoice'
    )
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, attrs):
        invoice = attrs.get('invoice')
        amount_paid = attrs.get('amount_paid')
        if amount_paid <= 0:
            raise serializers.ValidationError(
                {'amount_paid': _('Payment must be greater than zero.')}
            )
        if amount_paid > invoice.total_amount:
            raise serializers.ValidationError(
                {'amount_paid': _('Payment cannot exceed total amount.')}
            )
        return attrs

    def save(self, **kwargs):
        invoice = self.validated_data['invoice']
        amount_paid = self.validated_data['amount_paid']
        invoice.paid_amount += amount_paid
        if invoice.paid_amount >= invoice.total_amount:
            invoice.payment_status = 'PAID'
        invoice.save()
        return invoice

***