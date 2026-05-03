from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal
from .models import ReferralBonus
from ledger.services import LedgerService
from wallet.services import WalletService


class ReferralService:

    @staticmethod
    @db_transaction.atomic
    def approve_referral_bonus(bonus, admin_user):
        """Admin approves a referral bonus → credits referrer ledger."""
        if bonus.status != 'PENDING':
            raise ValueError(f"Cannot approve bonus with status: {bonus.status}")

        wallet = WalletService.get_wallet(bonus.referrer)

        LedgerService.credit(
            wallet=wallet,
            amount=bonus.amount,
            category='REFERRAL_BONUS',
            description=f"Referral bonus for inviting {bonus.referred_user.email}",
            reference=str(bonus.id),
            created_by=admin_user,
        )

        bonus.status = 'APPROVED'
        bonus.approved_by = admin_user
        bonus.approved_at = timezone.now()
        bonus.save(update_fields=['status', 'approved_by', 'approved_at'])
        return bonus

    @staticmethod
    @db_transaction.atomic
    def reject_referral_bonus(bonus, admin_user, note=''):
        if bonus.status != 'PENDING':
            raise ValueError(f"Cannot reject bonus with status: {bonus.status}")
        bonus.status = 'REJECTED'
        bonus.approved_by = admin_user
        bonus.approved_at = timezone.now()
        bonus.note = note
        bonus.save(update_fields=['status', 'approved_by', 'approved_at', 'note'])
        return bonus

    @staticmethod
    def create_pending_bonus(referrer, referred_user, amount):
        """Create a pending referral bonus awaiting admin approval."""
        return ReferralBonus.objects.create(
            referrer=referrer,
            referred_user=referred_user,
            amount=Decimal(str(amount)),
            status='PENDING',
        )
