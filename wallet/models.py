from django.db import models
from django.conf import settings
import uuid


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    wallet_id = models.CharField(max_length=20, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'

    def __str__(self):
        return f"Wallet({self.wallet_id}) - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.wallet_id:
            self.wallet_id = self._generate_wallet_id()
        super().save(*args, **kwargs)

    def _generate_wallet_id(self):
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        while True:
            wid = 'BRK-' + ''.join(random.choices(chars, k=10))
            if not Wallet.objects.filter(wallet_id=wid).exists():
                return wid

    @property
    def balance(self):
        """Ledger-derived balance ONLY — never stored directly."""
        from ledger.models import LedgerEntry
        from django.db.models import Sum
        result = LedgerEntry.objects.filter(
            wallet=self,
            entry_type='CREDIT',
            is_reversed=False
        ).aggregate(total=Sum('amount'))['total'] or 0

        debit = LedgerEntry.objects.filter(
            wallet=self,
            entry_type='DEBIT',
            is_reversed=False
        ).aggregate(total=Sum('amount'))['total'] or 0

        return result - debit

    @property
    def profit_balance(self):
        """Admin bonus credits only."""
        from ledger.models import LedgerEntry
        from django.db.models import Sum
        result = LedgerEntry.objects.filter(
            wallet=self,
            entry_type='CREDIT',
            category='ADMIN_BONUS',
            is_reversed=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        return result

    @property
    def referral_balance(self):
        """Admin-approved referral credits only."""
        from ledger.models import LedgerEntry
        from django.db.models import Sum
        result = LedgerEntry.objects.filter(
            wallet=self,
            entry_type='CREDIT',
            category='REFERRAL_BONUS',
            is_reversed=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        return result
