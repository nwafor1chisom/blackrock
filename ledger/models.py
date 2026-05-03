from django.db import models
from django.conf import settings
import uuid


class LedgerEntry(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]
    CATEGORY_CHOICES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('ADMIN_BONUS', 'Admin Bonus'),
        ('REFERRAL_BONUS', 'Referral Bonus'),
        ('FEE', 'Fee'),
        ('REVERSAL', 'Reversal'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        'wallet.Wallet',
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ledger_entries'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ledger_actions'
    )
    is_reversed = models.BooleanField(default=False)
    reversal_entry = models.OneToOneField(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reversed_by'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ledger_entries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'entry_type']),
            models.Index(fields=['wallet', 'category']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.entry_type} | {self.category} | {self.amount} | {self.wallet.wallet_id}"

    class LedgerIntegrityError(Exception):
        pass
