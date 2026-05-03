from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal
from .models import LedgerEntry
from wallet.models import Wallet


class LedgerService:
    """
    Core double-entry ledger engine.
    ALL balance changes MUST go through this service.
    NEVER update balances directly.
    """

    @staticmethod
    @db_transaction.atomic
    def credit(wallet, amount, category, description, reference='',
               transaction_obj=None, created_by=None, ip_address=None):
        """Credit a wallet (increase balance)."""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Credit amount must be positive.")

        entry = LedgerEntry.objects.create(
            wallet=wallet,
            entry_type='CREDIT',
            category=category,
            amount=amount,
            description=description,
            reference=reference,
            transaction=transaction_obj,
            created_by=created_by,
            ip_address=ip_address,
        )
        return entry

    @staticmethod
    @db_transaction.atomic
    def debit(wallet, amount, category, description, reference='',
              transaction_obj=None, created_by=None, ip_address=None):
        """Debit a wallet (decrease balance). Enforces sufficient funds."""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Debit amount must be positive.")

        current_balance = wallet.balance
        if current_balance < amount:
            raise InsufficientFundsError(
                f"Insufficient funds. Balance: {current_balance}, Required: {amount}"
            )

        entry = LedgerEntry.objects.create(
            wallet=wallet,
            entry_type='DEBIT',
            category=category,
            amount=amount,
            description=description,
            reference=reference,
            transaction=transaction_obj,
            created_by=created_by,
            ip_address=ip_address,
        )
        return entry

    @staticmethod
    @db_transaction.atomic
    def reverse_entry(entry, reason, reversed_by=None):
        """Reverse a ledger entry by creating an offsetting entry."""
        if entry.is_reversed:
            raise LedgerError("Entry has already been reversed.")

        # Create opposite entry
        reverse_type = 'DEBIT' if entry.entry_type == 'CREDIT' else 'CREDIT'
        reversal = LedgerEntry.objects.create(
            wallet=entry.wallet,
            entry_type=reverse_type,
            category='REVERSAL',
            amount=entry.amount,
            description=f"REVERSAL: {reason}",
            reference=f"REV-{entry.id}",
            created_by=reversed_by,
        )

        entry.is_reversed = True
        entry.reversal_entry = reversal
        entry.save(update_fields=['is_reversed', 'reversal_entry'])

        return reversal

    @staticmethod
    def get_balance(wallet):
        """Compute balance from ledger entries."""
        from django.db.models import Sum
        credits = LedgerEntry.objects.filter(
            wallet=wallet, entry_type='CREDIT', is_reversed=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        debits = LedgerEntry.objects.filter(
            wallet=wallet, entry_type='DEBIT', is_reversed=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return credits - debits

    @staticmethod
    def get_transaction_history(wallet, limit=50):
        return LedgerEntry.objects.filter(
            wallet=wallet
        ).select_related('transaction', 'created_by').order_by('-created_at')[:limit]


class InsufficientFundsError(Exception):
    pass


class LedgerError(Exception):
    pass
