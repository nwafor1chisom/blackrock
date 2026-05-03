from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from wallet.services import WalletService
from .models import LedgerEntry


@login_required
def history_view(request):
    wallet = WalletService.get_wallet(request.user)
    entries = LedgerEntry.objects.filter(wallet=wallet).order_by('-created_at')

    category = request.GET.get('category', '')
    entry_type = request.GET.get('type', '')

    if category:
        entries = entries.filter(category=category)
    if entry_type:
        entries = entries.filter(entry_type=entry_type)

    context = {
        'entries': entries[:100],
        'wallet': wallet,
        'category_choices': LedgerEntry.CATEGORY_CHOICES,
        'type_choices': LedgerEntry.ENTRY_TYPE_CHOICES,
        'selected_category': category,
        'selected_type': entry_type,
    }
    return render(request, 'ledger/history.html', context)
