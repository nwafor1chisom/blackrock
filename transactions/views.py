from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import DepositForm, WithdrawalForm
from .models import Transaction
from .services import DepositService, WithdrawalService
from wallet.services import WalletService
from payments.models import PaymentMethod


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0]
    return request.META.get('REMOTE_ADDR')


@login_required
def deposit_view(request):
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    if request.method == 'POST':
        form = DepositForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                txn = DepositService.create_deposit_request(
                    user=request.user,
                    amount=form.cleaned_data['amount'],
                    payment_method=form.cleaned_data['payment_method'],
                    sender_address=form.cleaned_data.get('sender_address', ''),
                    tx_hash=form.cleaned_data.get('tx_hash', ''),
                    payment_proof=form.cleaned_data.get('payment_proof'),
                    ip_address=get_client_ip(request),
                )
                messages.success(request, f'Deposit request submitted! Reference: {txn.reference}. Awaiting admin approval.')
                return redirect('transactions:deposit_confirm', pk=txn.pk)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = DepositForm()

    # Pre-fill plan name if navigated from plan page (?plan=PlanName)
    selected_plan = request.GET.get('plan', '')

    context = {
        'form': form,
        'payment_methods': payment_methods,
        'selected_plan': selected_plan,
    }
    return render(request, 'transactions/deposit.html', context)


@login_required
def deposit_confirm_view(request, pk):
    txn = get_object_or_404(Transaction, pk=pk, user=request.user, transaction_type='DEPOSIT')
    return render(request, 'transactions/deposit_confirm.html', {'txn': txn})


@login_required
def withdraw_view(request):
    wallet = WalletService.get_wallet(request.user)

    if not request.user.kyc_approved:
        messages.warning(request, 'You must complete KYC verification before withdrawals.')
        return redirect('kyc:submit')

    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            try:
                txn = WithdrawalService.create_withdrawal_request(
                    user=request.user,
                    amount=form.cleaned_data['amount'],
                    withdrawal_address=form.cleaned_data['withdrawal_address'],
                    withdrawal_network=form.cleaned_data['withdrawal_network'],
                    ip_address=get_client_ip(request),
                )
                messages.success(request, f'Withdrawal request submitted! Reference: {txn.reference}. Awaiting admin approval.')
                return redirect('transactions:history')
            except PermissionError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = WithdrawalForm()

    return render(request, 'transactions/withdraw.html', {
        'form': form,
        'wallet': wallet,
        'balance': wallet.balance,
    })


@login_required
def history_view(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')

    tx_type = request.GET.get('type', '')
    status = request.GET.get('status', '')

    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
    if status:
        transactions = transactions.filter(status=status)

    context = {
        'transactions': transactions[:100],
        'type_choices': Transaction.TYPE_CHOICES,
        'status_choices': Transaction.STATUS_CHOICES,
        'selected_type': tx_type,
        'selected_status': status,
    }
    return render(request, 'transactions/history.html', context)
