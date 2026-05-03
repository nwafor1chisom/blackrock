from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from decimal import Decimal

from transactions.models import Transaction
from transactions.services import DepositService, WithdrawalService
from kyc.models import KYCProfile
from ledger.models import LedgerEntry
from ledger.services import LedgerService
from wallet.services import WalletService
from referral.models import ReferralBonus
from referral.services import ReferralService
from payments.models import PaymentMethod
from django.contrib.auth import get_user_model

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    pending_deposits = Transaction.objects.filter(transaction_type='DEPOSIT', status='PENDING').count()
    pending_withdrawals = Transaction.objects.filter(transaction_type='WITHDRAWAL', status='PENDING').count()
    pending_kyc = KYCProfile.objects.filter(status='PENDING').count()
    pending_referrals = ReferralBonus.objects.filter(status='PENDING').count()

    total_deposited = Transaction.objects.filter(
        transaction_type='DEPOSIT', status='APPROVED'
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_withdrawn = Transaction.objects.filter(
        transaction_type='WITHDRAWAL', status='APPROVED'
    ).aggregate(total=Sum('amount'))['total'] or 0

    recent_txns = Transaction.objects.order_by('-created_at')[:10]

    context = {
        'total_users': total_users,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'pending_kyc': pending_kyc,
        'pending_referrals': pending_referrals,
        'total_deposited': total_deposited,
        'total_withdrawn': total_withdrawn,
        'recent_txns': recent_txns,
    }
    return render(request, 'adminpanel/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_deposits(request):
    status = request.GET.get('status', 'PENDING')
    deposits = Transaction.objects.filter(
        transaction_type='DEPOSIT'
    ).select_related('user', 'payment_method').order_by('-created_at')

    if status:
        deposits = deposits.filter(status=status)

    return render(request, 'adminpanel/deposits.html', {
        'deposits': deposits,
        'status_choices': Transaction.STATUS_CHOICES,
        'selected_status': status,
    })


@login_required
@user_passes_test(is_admin)
def admin_deposit_action(request, pk):
    txn = get_object_or_404(Transaction, pk=pk, transaction_type='DEPOSIT')
    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('note', '')
        try:
            if action == 'approve':
                DepositService.approve_deposit(txn, request.user, note)
                messages.success(request, f'Deposit {txn.reference} approved and credited.')
            elif action == 'reject':
                DepositService.reject_deposit(txn, request.user, note)
                messages.warning(request, f'Deposit {txn.reference} rejected.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('adminpanel:deposits')


@login_required
@user_passes_test(is_admin)
def admin_withdrawals(request):
    status = request.GET.get('status', 'PENDING')
    withdrawals = Transaction.objects.filter(
        transaction_type='WITHDRAWAL'
    ).select_related('user').order_by('-created_at')

    if status:
        withdrawals = withdrawals.filter(status=status)

    return render(request, 'adminpanel/withdrawals.html', {
        'withdrawals': withdrawals,
        'status_choices': Transaction.STATUS_CHOICES,
        'selected_status': status,
    })


@login_required
@user_passes_test(is_admin)
def admin_withdrawal_action(request, pk):
    txn = get_object_or_404(Transaction, pk=pk, transaction_type='WITHDRAWAL')
    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('note', '')
        try:
            if action == 'approve':
                WithdrawalService.approve_withdrawal(txn, request.user, note)
                messages.success(request, f'Withdrawal {txn.reference} approved.')
            elif action == 'reject':
                WithdrawalService.reject_withdrawal(txn, request.user, note)
                messages.warning(request, f'Withdrawal {txn.reference} rejected and funds restored.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('adminpanel:withdrawals')


@login_required
@user_passes_test(is_admin)
def admin_kyc(request):
    status = request.GET.get('status', 'PENDING')
    profiles = KYCProfile.objects.select_related('user').order_by('-submitted_at')

    if status:
        profiles = profiles.filter(status=status)

    return render(request, 'adminpanel/kyc.html', {
        'profiles': profiles,
        'status_choices': KYCProfile.STATUS_CHOICES,
        'selected_status': status,
    })


@login_required
@user_passes_test(is_admin)
def admin_kyc_action(request, pk):
    profile = get_object_or_404(KYCProfile, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        reason = request.POST.get('rejection_reason', '')
        if action == 'approve':
            profile.status = 'APPROVED'
            profile.reviewed_by = request.user
            profile.reviewed_at = timezone.now()
            profile.save()
            messages.success(request, f'KYC for {profile.user.email} approved.')
        elif action == 'reject':
            profile.status = 'REJECTED'
            profile.rejection_reason = reason
            profile.reviewed_by = request.user
            profile.reviewed_at = timezone.now()
            profile.save()
            messages.warning(request, f'KYC for {profile.user.email} rejected.')
    return redirect('adminpanel:kyc')


@login_required
@user_passes_test(is_admin)
def admin_credit_bonus(request):
    """Admin manually credits profit (admin bonus) to a user wallet."""
    users = User.objects.all().order_by('email')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        amount = request.POST.get('amount')
        description = request.POST.get('description', 'Admin profit bonus')

        try:
            target_user = User.objects.get(pk=user_id)
            wallet = WalletService.get_wallet(target_user)
            LedgerService.credit(
                wallet=wallet,
                amount=Decimal(str(amount)),
                category='ADMIN_BONUS',
                description=description,
                created_by=request.user,
            )
            messages.success(request, f'${amount} bonus credited to {target_user.email}')
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'adminpanel/credit_bonus.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def admin_referrals(request):
    bonuses = ReferralBonus.objects.select_related(
        'referrer', 'referred_user'
    ).order_by('-created_at')
    status = request.GET.get('status', 'PENDING')
    if status:
        bonuses = bonuses.filter(status=status)

    return render(request, 'adminpanel/referrals.html', {
        'bonuses': bonuses,
        'selected_status': status,
    })


@login_required
@user_passes_test(is_admin)
def admin_referral_action(request, pk):
    bonus = get_object_or_404(ReferralBonus, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'approve':
                ReferralService.approve_referral_bonus(bonus, request.user)
                messages.success(request, 'Referral bonus approved and credited.')
            elif action == 'reject':
                ReferralService.reject_referral_bonus(bonus, request.user)
                messages.warning(request, 'Referral bonus rejected.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('adminpanel:referrals')


@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.select_related('wallet').order_by('-date_joined')
    return render(request, 'adminpanel/users.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    wallet = WalletService.get_wallet(target_user)
    transactions = Transaction.objects.filter(user=target_user).order_by('-created_at')[:20]
    ledger_entries = LedgerEntry.objects.filter(wallet=wallet).order_by('-created_at')[:20]

    try:
        kyc = target_user.kyc_profile
    except Exception:
        kyc = None

    context = {
        'target_user': target_user,
        'wallet': wallet,
        'transactions': transactions,
        'ledger_entries': ledger_entries,
        'kyc': kyc,
    }
    return render(request, 'adminpanel/user_detail.html', context)
