from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal
from .models import Transaction
from ledger.services import LedgerService, InsufficientFundsError
from wallet.services import WalletService


class DepositService:

    @staticmethod
    def create_deposit_request(user, amount, payment_method, sender_address='',
                                tx_hash='', payment_proof=None, ip_address=None):
        """User initiates a deposit request. Status = PENDING until admin approves."""
        wallet = WalletService.get_wallet(user)
        amount = Decimal(str(amount))

        if amount < payment_method.minimum_deposit:
            raise ValueError(f"Minimum deposit is ${payment_method.minimum_deposit}")

        # Prevent duplicate pending deposits
        existing = Transaction.objects.filter(
            user=user,
            transaction_type='DEPOSIT',
            status='PENDING',
            tx_hash=tx_hash
        ).exists()
        if tx_hash and existing:
            raise ValueError("A deposit with this transaction hash already exists.")

        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='DEPOSIT',
            status='PENDING',
            amount=amount,
            payment_method=payment_method,
            sender_address=sender_address,
            tx_hash=tx_hash,
            payment_proof=payment_proof,
            ip_address=ip_address,
        )
        return txn

    @staticmethod
    @db_transaction.atomic
    def approve_deposit(transaction, admin_user, note=''):
        """Admin approves a deposit → credits user's ledger."""
        if transaction.transaction_type != 'DEPOSIT':
            raise ValueError("This is not a deposit transaction.")
        if transaction.status != 'PENDING':
            raise ValueError(f"Cannot approve transaction with status: {transaction.status}")

        # Credit ledger
        LedgerService.credit(
            wallet=transaction.wallet,
            amount=transaction.amount,
            category='DEPOSIT',
            description=f"Deposit approved | Ref: {transaction.reference}",
            reference=transaction.reference,
            transaction_obj=transaction,
            created_by=admin_user,
        )

        transaction.status = 'APPROVED'
        transaction.reviewed_by = admin_user
        transaction.reviewed_at = timezone.now()
        transaction.admin_note = note
        transaction.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_note'])
        return transaction

    @staticmethod
    @db_transaction.atomic
    def reject_deposit(transaction, admin_user, note=''):
        """Admin rejects a deposit request."""
        if transaction.status != 'PENDING':
            raise ValueError(f"Cannot reject transaction with status: {transaction.status}")

        transaction.status = 'REJECTED'
        transaction.reviewed_by = admin_user
        transaction.reviewed_at = timezone.now()
        transaction.admin_note = note
        transaction.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_note'])
        return transaction


class WithdrawalService:

    @staticmethod
    @db_transaction.atomic
    def create_withdrawal_request(user, amount, withdrawal_address, withdrawal_network, ip_address=None):
        """User requests a withdrawal. Requires KYC approval first."""
        if not user.kyc_approved:
            raise PermissionError("KYC verification required before withdrawals.")

        wallet = WalletService.get_wallet(user)
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")

        if wallet.balance < amount:
            raise InsufficientFundsError("Insufficient wallet balance.")

        # Reserve funds via debit pending admin review
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='WITHDRAWAL',
            status='PENDING',
            amount=amount,
            withdrawal_address=withdrawal_address,
            withdrawal_network=withdrawal_network,
            ip_address=ip_address,
        )

        # Debit immediately to reserve the funds
        LedgerService.debit(
            wallet=wallet,
            amount=amount,
            category='WITHDRAWAL',
            description=f"Withdrawal request pending | Ref: {txn.reference}",
            reference=txn.reference,
            transaction_obj=txn,
            created_by=user,
            ip_address=ip_address,
        )
        return txn

    @staticmethod
    @db_transaction.atomic
    def approve_withdrawal(transaction, admin_user, note=''):
        """Admin approves withdrawal — funds already debited, just marks as done."""
        if transaction.transaction_type != 'WITHDRAWAL':
            raise ValueError("Not a withdrawal transaction.")
        if transaction.status != 'PENDING':
            raise ValueError(f"Cannot approve status: {transaction.status}")

        transaction.status = 'APPROVED'
        transaction.reviewed_by = admin_user
        transaction.reviewed_at = timezone.now()
        transaction.admin_note = note
        transaction.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_note'])
        return transaction

    @staticmethod
    @db_transaction.atomic
    def reject_withdrawal(transaction, admin_user, note=''):
        """Admin rejects withdrawal — reverse the debit to restore funds."""
        if transaction.status != 'PENDING':
            raise ValueError(f"Cannot reject status: {transaction.status}")

        # Reverse the debit entry to restore balance
        debit_entry = transaction.ledger_entries.filter(entry_type='DEBIT').first()
        if debit_entry:
            LedgerService.reverse_entry(
                debit_entry,
                reason=f"Withdrawal rejected by admin: {note}",
                reversed_by=admin_user
            )

        transaction.status = 'REJECTED'
        transaction.reviewed_by = admin_user
        transaction.reviewed_at = timezone.now()
        transaction.admin_note = note
        transaction.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_note'])
        return transaction
