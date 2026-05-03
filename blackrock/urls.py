"""
Main URL configuration.

URL hierarchy:
  /              → core.urls (public site, app_name='public')
  /users/        → users.urls (auth: login, register, logout, profile, OTP reset)
  /dashboard/    → dashboard.urls (authenticated dashboard)
  /wallet/       → wallet.urls
  /ledger/       → ledger.urls
  /transactions/ → transactions.urls
  /kyc/          → kyc.urls
  /payments/     → payments.urls
  /referral/     → referral.urls
  /adminpanel/   → adminpanel.urls
  /admin/        → Django admin

Loop prevention:
  - '/' is handled ONLY by core.urls → index_view
  - index_view renders for guests, redirects auth→dashboard
  - index_view NEVER redirects to 'public:home' (which resolves back to '/')
  - PublicRouteGuard middleware intercepts authenticated access to all public paths
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Authenticated platform ─────────────────────────────────────────────
    # Listed BEFORE '' so Django matches these specific paths first
    path('users/',        include('users.urls')),
    path('dashboard/',    include('dashboard.urls')),
    path('wallet/',       include('wallet.urls')),
    path('ledger/',       include('ledger.urls')),
    path('transactions/', include('transactions.urls')),
    path('kyc/',          include('kyc.urls')),
    path('payments/',     include('payments.urls')),
    path('referral/',     include('referral.urls')),
    path('adminpanel/',   include('adminpanel.urls')),

    # ── Public marketing site ──────────────────────────────────────────────
    # '' must come LAST so it only catches paths not matched above
    path('', include('core.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
