"""
core/middleware.py

Three middleware classes, executed in order:

1. PublicRouteGuard     — If authenticated, intercept ANY public URL and redirect
                          to dashboard:home. Implements the SaaS-level lock.

2. AuditLogMiddleware   — Log authenticated POST actions to DB + console.

3. KYCEnforcementMiddleware — Block withdrawal routes for non-KYC users.
"""

from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404
import logging

logger = logging.getLogger('blackrock.audit')


# ── 1. PUBLIC ROUTE GUARD (SAAS-LEVEL AUTH LOCK) ──────────────────────────

class PublicRouteGuard:
    """
    If an authenticated user tries to access any public route
    (home, login, register, about, plan, faq, blog, contact, certification,
    password reset steps), redirect immediately to dashboard:home.

    This is the single enforcement point — views do NOT need to repeat this.

    Exempt from guarding:
      - All /dashboard/ routes (the destination)
      - All /admin/ routes
      - All authenticated-platform routes:
          /users/logout/, /wallet/, /ledger/, /transactions/,
          /kyc/, /payments/, /referral/, /adminpanel/
      - Static/media files
    """

    # Paths that authenticated users MUST be redirected away from
    PUBLIC_PREFIXES = (
        '/',            # root — covers home
        '/about/',
        '/plan/',
        '/faq/',
        '/blog/',
        '/certification/',
        '/contact/',
        '/users/login/',
        '/users/register/',
        '/users/forgot-password/',
        '/users/verify-otp/',
        '/users/reset-password/',
    )

    # Paths that are ALWAYS allowed regardless of auth status
    ALWAYS_ALLOW_PREFIXES = (
        '/dashboard/',
        '/wallet/',
        '/ledger/',
        '/transactions/',
        '/kyc/',
        '/payments/',
        '/referral/',
        '/adminpanel/',
        '/admin/',
        '/users/logout/',
        '/users/profile/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path

            # Never intercept always-allowed paths
            if any(path.startswith(p) for p in self.ALWAYS_ALLOW_PREFIXES):
                return self.get_response(request)

            # Intercept any public path
            if any(path == p or path.startswith(p) for p in self.PUBLIC_PREFIXES):
                return redirect(reverse('dashboard:home'))

        return self.get_response(request)


# ── 2. AUDIT LOG MIDDLEWARE ────────────────────────────────────────────────

class AuditLogMiddleware:
    """Log authenticated POST actions to AuditLog model and console."""

    AUDIT_PATHS = {
        '/transactions/deposit/':  'DEPOSIT_SUBMIT',
        '/transactions/withdraw/': 'WITHDRAW_SUBMIT',
        '/kyc/submit/':            'KYC_SUBMIT',
        '/users/login/':           'LOGIN',
        '/users/logout/':          'LOGOUT',
        '/contact/':               'ADMIN_ACTION',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.method == 'POST':
            action = self._resolve_action(request.path)
            if action:
                try:
                    from core.models import AuditLog
                    AuditLog.log(
                        action=action,
                        description=f'{action} via {request.path}',
                        user=request.user,
                        request=request,
                    )
                except Exception:
                    pass

            logger.info(
                f'[AUDIT] user={request.user.email} '
                f'path={request.path} '
                f'ip={self._get_ip(request)} '
                f'status={response.status_code}'
            )

        return response

    def _resolve_action(self, path):
        for prefix, action in self.AUDIT_PATHS.items():
            if path.startswith(prefix):
                return action
        if '/adminpanel/' in path:
            return 'ADMIN_ACTION'
        return None

    def _get_ip(self, request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        return forwarded.split(',')[0] if forwarded else request.META.get('REMOTE_ADDR', '')


# ── 3. KYC ENFORCEMENT MIDDLEWARE ─────────────────────────────────────────

class KYCEnforcementMiddleware:
    """Block /transactions/withdraw/ for users whose KYC is not approved."""

    PROTECTED_PATHS = ['/transactions/withdraw/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and any(request.path.startswith(p) for p in self.PROTECTED_PATHS)
            and not request.user.kyc_approved
        ):
            from django.contrib import messages
            messages.warning(request, 'KYC verification is required before withdrawals.')
            return redirect(reverse('kyc:submit'))

        return self.get_response(request)
