from django.db import models
from django.conf import settings
import uuid
from cloudinary.models import CloudinaryField


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    TYPE_CHOICES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=30, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    wallet = models.ForeignKey(
        'wallet.Wallet',
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    amount = models.DecimalField(max_digits=20, decimal_places=8)

    # Deposit fields
    payment_method = models.ForeignKey(
        'payments.PaymentMethod',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='transactions'
    )
    payment_proof = CloudinaryField('image', folder='payment_proofs', blank=True, null=True)
    sender_address = models.CharField(max_length=255, blank=True, help_text='TX hash or sender wallet')
    tx_hash = models.CharField(max_length=255, blank=True)

    # Withdrawal fields
    withdrawal_address = models.CharField(max_length=255, blank=True)
    withdrawal_network = models.CharField(max_length=50, blank=True)

    # Admin action
    admin_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_transactions'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_type', 'status']),
        ]

    def __str__(self):
        return f"{self.reference} | {self.transaction_type} | {self.amount} | {self.status}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)

    def _generate_reference(self):
        import random
        import string
        prefix = 'DEP' if self.transaction_type == 'DEPOSIT' else 'WDR'
        suffix = ''.join(random.choices(string.digits + string.ascii_uppercase, k=10))
        return f"{prefix}-{suffix}"