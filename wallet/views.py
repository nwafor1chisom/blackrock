from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import WalletService
from ledger.models import LedgerEntry


@login_required
def wallet_view(request):
    wallet = WalletService.get_wallet(request.user)
    recent_entries = LedgerEntry.objects.filter(
        wallet=wallet
    ).select_related('transaction').order_by('-created_at')[:10]

    context = {
        'wallet': wallet,
        'balance': wallet.balance,
        'profit_balance': wallet.profit_balance,
        'referral_balance': wallet.referral_balance,
        'recent_entries': recent_entries,
    }
    return render(request, 'wallet/wallet.html', context)
