"""
Password reset — 3-step OTP flow.

Step 1  /users/forgot-password/         — Enter email → receive OTP
Step 2  /users/verify-otp/<token>/      — Enter 6-digit OTP
Step 3  /users/reset-password/<token>/  — Set new password

All 3 views are in PUBLIC_PREFIXES in PublicRouteGuard so authenticated
users are redirected to dashboard before any of these views execute.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

from .models import PasswordResetOTP
from .otp_email import OTPEmailService
from .reset_forms import ForgotPasswordForm, OTPVerificationForm, SetNewPasswordForm

logger = logging.getLogger('blackrock.otp')
User = get_user_model()


def _get_ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    return fwd.split(',')[0].strip() if fwd else request.META.get('REMOTE_ADDR', '')


def _get_ua(request):
    return request.META.get('HTTP_USER_AGENT', '')


OTP_ERROR_MESSAGES = {
    'USED':         'This OTP has already been used. Please request a new one.',
    'INVALIDATED':  'This OTP is no longer valid. Please request a new one.',
    'EXPIRED':      'Your OTP has expired (valid for 10 minutes). Please request a new one.',
    'MAX_ATTEMPTS': 'Too many incorrect attempts. Please request a new OTP.',
    'INVALID':      'Invalid OTP. Please check the code and try again.',
}


# ── Step 1: Request OTP ────────────────────────────────────────────────────

@never_cache
@require_http_methods(['GET', 'POST'])
def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            GENERIC = (
                f'If that email is registered, a 6-digit OTP has been sent. '
                f'It expires in {PasswordResetOTP.OTP_EXPIRY_MINUTES} minutes. '
                f'Check your inbox and spam folder.'
            )

            try:
                user = User.objects.get(email__iexact=email, is_active=True)
            except User.DoesNotExist:
                # Never reveal whether email exists
                messages.success(request, GENERIC)
                return redirect('users:forgot_password')

            # Rate limit check
            allowed, wait_secs = PasswordResetOTP.check_rate_limit(user)
            if not allowed:
                wait_mins = max(1, wait_secs // 60)
                messages.error(
                    request,
                    f'Too many OTP requests. Please wait {wait_mins} minute(s).'
                )
                logger.warning(f'[OTP RATE LIMIT] user={user.email} ip={_get_ip(request)}')
                return render(request, 'users/forgot_password.html', {'form': form})

            # Create OTP (hashed, previous OTPs invalidated)
            otp_instance, otp_plain = PasswordResetOTP.create_for_user(
                user=user,
                ip_address=_get_ip(request),
                user_agent=_get_ua(request),
            )

            # Send OTP via email with retry
            result = OTPEmailService.send_otp_email(
                user=user,
                otp_plaintext=otp_plain,
                expires_minutes=PasswordResetOTP.OTP_EXPIRY_MINUTES,
                otp_instance=otp_instance,
                ip_address=_get_ip(request),
            )

            if result['success']:
                logger.info(
                    f'[OTP SENT] user={user.email} '
                    f'token={otp_instance.reset_token} '
                    f'provider={result["provider"]} '
                    f'attempts={result["attempts"]}'
                )
                messages.success(request, GENERIC)
                return redirect('users:verify_otp', token=str(otp_instance.reset_token))
            else:
                # Email failed — invalidate the OTP
                otp_instance.is_invalidated = True
                otp_instance.save(update_fields=['is_invalidated'])

                from django.conf import settings
                if getattr(settings, 'DEBUG', False):
                    # DEBUG: OTP was printed to console — allow user to proceed
                    messages.warning(
                        request,
                        f'⚠ Email delivery failed. DEBUG MODE: check server console for OTP.'
                    )
                    # Re-create so user can still proceed in dev
                    otp_instance2, otp_plain2 = PasswordResetOTP.create_for_user(
                        user=user,
                        ip_address=_get_ip(request),
                        user_agent=_get_ua(request),
                    )
                    from .otp_email import OTPEmailConfig
                    OTPEmailConfig.DEBUG_PRINT_OTP = True
                    OTPEmailService._debug_print(user.email, otp_plain2, PasswordResetOTP.OTP_EXPIRY_MINUTES)
                    return redirect('users:verify_otp', token=str(otp_instance2.reset_token))
                else:
                    messages.error(
                        request,
                        'Failed to send OTP after multiple attempts. '
                        'Please try again or contact support.'
                    )
                    return render(request, 'users/forgot_password.html', {'form': form})
    else:
        form = ForgotPasswordForm()

    return render(request, 'users/forgot_password.html', {'form': form})


# ── Step 2: Verify OTP ─────────────────────────────────────────────────────

@never_cache
@require_http_methods(['GET', 'POST'])
def verify_otp_view(request, token):
    otp_instance = get_object_or_404(
        PasswordResetOTP,
        reset_token=token,
        is_used=False,
        is_invalidated=False,
    )

    if otp_instance.is_expired:
        return render(request, 'users/otp_expired.html', {
            'email': otp_instance.user.email
        })

    can_resend, resend_wait = PasswordResetOTP.check_resend_cooldown(otp_instance.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'verify')

        # ── Resend ──
        if action == 'resend':
            if not can_resend:
                messages.error(request, f'Please wait {resend_wait}s before resending.')
            else:
                allowed, wait_secs = PasswordResetOTP.check_rate_limit(otp_instance.user)
                if not allowed:
                    messages.error(request, f'Too many requests. Wait {max(1, wait_secs//60)} min.')
                else:
                    new_instance, otp_plain = PasswordResetOTP.create_for_user(
                        user=otp_instance.user,
                        ip_address=_get_ip(request),
                        user_agent=_get_ua(request),
                    )
                    result = OTPEmailService.send_otp_email(
                        user=otp_instance.user,
                        otp_plaintext=otp_plain,
                        expires_minutes=PasswordResetOTP.OTP_EXPIRY_MINUTES,
                        otp_instance=new_instance,
                        ip_address=_get_ip(request),
                    )
                    if result['success']:
                        messages.success(request, 'A new OTP has been sent to your email.')
                        logger.info(f'[OTP RESENT] user={otp_instance.user.email}')
                    else:
                        from django.conf import settings
                        if getattr(settings, 'DEBUG', False):
                            messages.warning(request, 'Email failed — check server console for OTP.')
                        else:
                            messages.error(request, 'Failed to resend OTP. Try again.')
                    return redirect('users:verify_otp', token=str(new_instance.reset_token))
            return redirect('users:verify_otp', token=str(token))

        # ── Verify ──
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_instance.refresh_from_db()

            if otp_instance.is_expired:
                return render(request, 'users/otp_expired.html', {
                    'email': otp_instance.user.email
                })

            success, error_code = otp_instance.verify(form.cleaned_data['otp'])

            if success:
                # Store session verification flag
                request.session[f'otp_verified_{token}'] = True
                request.session[f'otp_user_{token}']     = str(otp_instance.user.pk)
                request.session.set_expiry(1800)
                logger.info(f'[OTP VERIFIED] user={otp_instance.user.email} ip={_get_ip(request)}')
                return redirect('users:reset_password', token=token)
            else:
                if error_code in ('EXPIRED',):
                    return render(request, 'users/otp_expired.html', {
                        'email': otp_instance.user.email
                    })
                if error_code in ('USED', 'INVALIDATED', 'MAX_ATTEMPTS'):
                    messages.error(request, OTP_ERROR_MESSAGES.get(error_code))
                    return redirect('users:forgot_password')

                remaining = otp_instance.attempts_remaining
                msg = OTP_ERROR_MESSAGES.get('INVALID')
                if remaining > 0:
                    messages.error(request, f'{msg} {remaining} attempt(s) remaining.')
                else:
                    messages.error(request, OTP_ERROR_MESSAGES.get('MAX_ATTEMPTS'))
                    return redirect('users:forgot_password')
                logger.warning(
                    f'[OTP WRONG] user={otp_instance.user.email} '
                    f'attempts={otp_instance.verify_attempts} '
                    f'ip={_get_ip(request)}'
                )
    else:
        form = OTPVerificationForm()

    from django.conf import settings
    context = {
        'form':             form,
        'token':            token,
        'email':            otp_instance.user.email,
        'expires_at':       otp_instance.expires_at,
        'seconds_remaining': otp_instance.seconds_remaining,
        'minutes_remaining': otp_instance.minutes_remaining,
        'attempts_remaining': otp_instance.attempts_remaining,
        'can_resend':       can_resend,
        'resend_wait':      resend_wait,
        'resend_cooldown':  PasswordResetOTP.OTP_RESEND_COOLDOWN_SEC,
        'delivery_status':  otp_instance.delivery_status,
        'debug_mode':       getattr(settings, 'DEBUG', False),
    }
    return render(request, 'users/verify_otp.html', context)


# ── Step 3: Reset Password ─────────────────────────────────────────────────

@never_cache
@require_http_methods(['GET', 'POST'])
def reset_password_view(request, token):
    # Guard: OTP must have been verified in this session
    if not request.session.get(f'otp_verified_{token}'):
        messages.error(request, 'Please verify your OTP first.')
        return redirect('users:verify_otp', token=token)

    otp_instance = get_object_or_404(
        PasswordResetOTP,
        reset_token=token,
        is_used=False,
        is_invalidated=False,
    )

    if otp_instance.is_expired:
        _clear_session(request, token)
        return render(request, 'users/otp_expired.html', {
            'email': otp_instance.user.email
        })

    # Session fixation guard: user in session must match OTP's user
    if str(otp_instance.user.pk) != request.session.get(f'otp_user_{token}'):
        _clear_session(request, token)
        messages.error(request, 'Session mismatch. Please restart the process.')
        return redirect('users:forgot_password')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user = otp_instance.user
            user.set_password(form.cleaned_data['password1'])
            user.save(update_fields=['password'])

            # Mark OTP consumed — single-use enforced
            otp_instance.mark_used()

            # Destroy reset session keys
            _clear_session(request, token)

            # Audit log
            try:
                from core.models import AuditLog
                AuditLog.log(
                    'ADMIN_ACTION',
                    f'Password reset completed for {user.email}',
                    user, request
                )
            except Exception:
                pass

            logger.info(f'[PASSWORD RESET] user={user.email} ip={_get_ip(request)}')
            messages.success(
                request,
                'Password reset successfully. Please log in with your new password.'
            )
            return redirect('users:login')
    else:
        form = SetNewPasswordForm()

    return render(request, 'users/reset_password.html', {
        'form':  form,
        'token': token,
        'email': otp_instance.user.email,
    })


def _clear_session(request, token):
    request.session.pop(f'otp_verified_{token}', None)
    request.session.pop(f'otp_user_{token}', None)
