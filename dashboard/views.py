from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from wallet.services import WalletService
from transactions.models import Transaction
from ledger.models import LedgerEntry
from payments.models import PaymentMethod


@login_required
def dashboard_home(request):
    user = request.user
    wallet = WalletService.get_wallet(user)

    recent_transactions = Transaction.objects.filter(
        user=user
    ).order_by('-created_at')[:5]

    recent_ledger = LedgerEntry.objects.filter(
        wallet=wallet
    ).order_by('-created_at')[:5]

    pending_deposits = Transaction.objects.filter(
        user=user, transaction_type='DEPOSIT', status='PENDING'
    ).count()

    pending_withdrawals = Transaction.objects.filter(
        user=user, transaction_type='WITHDRAWAL', status='PENDING'
    ).count()

    active_payment_methods = PaymentMethod.objects.filter(is_active=True).count()

    context = {
        'wallet': wallet,
        'balance': wallet.balance,
        'profit_balance': wallet.profit_balance,
        'referral_balance': wallet.referral_balance,
        'recent_transactions': recent_transactions,
        'recent_ledger': recent_ledger,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'active_payment_methods': active_payment_methods,
        'kyc_status': user.kyc_status,
        'kyc_approved': user.kyc_approved,
    }
    return render(request, 'dashboard/home.html', context)
