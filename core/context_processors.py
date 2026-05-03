from django.conf import settings
from wallet.services import WalletService
from transactions.models import Transaction


def global_context(request):
    """
    Inject global context into ALL templates (authenticated + public).
    - Authenticated users get wallet/balance/KYC data
    - All pages get WhatsApp number and site-wide settings
    """
    ctx = {
        'whatsapp_number': getattr(settings, 'WHATSAPP_NUMBER', ''),
        'contact_email':   getattr(settings, 'CONTACT_ADMIN_EMAIL', ''),
        'site_name':       'BlackRock',
    }

    if request.user.is_authenticated:
        try:
            wallet = WalletService.get_wallet(request.user)
            ctx['g_wallet']            = wallet
            ctx['g_balance']           = wallet.balance
            ctx['g_profit']            = wallet.profit_balance
            ctx['g_referral']          = wallet.referral_balance
            ctx['g_kyc_status']        = request.user.kyc_status
            ctx['g_kyc_approved']      = request.user.kyc_approved
            ctx['g_pending_deposits']  = Transaction.objects.filter(
                user=request.user, status='PENDING', transaction_type='DEPOSIT'
            ).count()
        except Exception:
            pass

    return ctx
