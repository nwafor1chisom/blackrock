from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import ReferralBonus
from wallet.services import WalletService

User = get_user_model()


@login_required
def referral_dashboard_view(request):
    user = request.user
    wallet = WalletService.get_wallet(user)

    referrals = User.objects.filter(referred_by=user).order_by('-date_joined')
    bonuses = ReferralBonus.objects.filter(referrer=user).order_by('-created_at')

    context = {
        'referral_code': user.referral_code,
        'referral_link': request.build_absolute_uri(f'/users/register/?ref={user.referral_code}'),
        'referrals': referrals,
        'bonuses': bonuses,
        'referral_balance': wallet.referral_balance,
        'total_referrals': referrals.count(),
        'approved_bonuses': bonuses.filter(status='APPROVED').count(),
    }
    return render(request, 'referral/dashboard.html', context)
