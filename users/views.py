"""
users/views.py — Auth views.

Auth guards in middleware (PublicRouteGuard) redirect authenticated users
away from /users/login/ and /users/register/ before these views run.
The checks inside views are belt-and-suspenders only.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm
from wallet.services import WalletService

User = get_user_model()


# ── Register ───────────────────────────────────────────────────────────────

@never_cache
@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            ref_code = form.cleaned_data.get('referral_code')
            if ref_code:
                try:
                    referrer = User.objects.get(referral_code=ref_code)
                    user.referred_by = referrer
                except User.DoesNotExist:
                    pass
            user.save()
            WalletService.create_wallet(user)
            messages.success(request, 'Account created! Please log in.')
            return redirect('users:login')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


# ── Login ──────────────────────────────────────────────────────────────────

@never_cache
@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        email    = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            # Always redirect to dashboard — no ?next= bypass
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid email or password.')

    form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})


# ── Logout ─────────────────────────────────────────────────────────────────

def logout_view(request):
    """
    The ONLY exit from the authenticated zone.
    Clears the full session, then redirects to '/'.
    index_view renders home.html for the now-unauthenticated user — no loop.
    """
    logout(request)
    return redirect('/')


# ── Profile (authenticated only) ───────────────────────────────────────────

@login_required(login_url='users:login')
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('users:profile')
    else:
        form = UserProfileUpdateForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})
