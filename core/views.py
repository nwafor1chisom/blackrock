"""
core/views.py — Public site views.

ROOT CONTRACT:
  GET /  + guest         → render public/home.html   (NEVER redirect to public:home)
  GET /  + authenticated → redirect to dashboard:home

PUBLIC ZONE (/about/, /plan/, /faq/, /blog/, /certification/):
  Render for EVERYONE — no auth check, no redirects.

CONTACT /contact/:
  GET  — authenticated only (redirect guests to login)
  POST — authenticated only (AJAX; save to DB + send auto-reply)
"""

import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from .models import InvestmentPlan, ContactMessage

logger = logging.getLogger('blackrock.core')


def _get_ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    return fwd.split(',')[0].strip() if fwd else request.META.get('REMOTE_ADDR', '')


# ── ROOT ───────────────────────────────────────────────────────────────────

def index_view(request):
    """
    Single handler for '/'.
    Renders home.html for guests — NEVER redirects to 'public:home'
    (that URL resolves back here → loop).
    Authenticated users already redirected by middleware; guard kept for safety.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    plans = InvestmentPlan.objects.filter(is_active=True)[:4]
    return render(request, 'public/home.html', {'plans': plans})


# ── STATIC PUBLIC PAGES (render for everyone) ─────────────────────────────

def about_view(request):
    return render(request, 'public/about.html')


def faq_view(request):
    return render(request, 'public/faq.html')


def blog_view(request):
    return render(request, 'public/blog.html')


def certification_view(request):
    return render(request, 'public/certification.html')


# ── PLAN PAGE ──────────────────────────────────────────────────────────────

def plan_view(request):
    """
    100% database-driven. Admin manages plans at /admin/core/investmentplan/.
    'Invest Now' → authenticated users open deposit modal,
                   guests are redirected to register.
    """
    plans = InvestmentPlan.objects.filter(is_active=True)
    return render(request, 'public/plan.html', {
        'plans': plans,
        'user_authenticated': request.user.is_authenticated,
    })


# ── CONTACT (PUBLIC SUPPORT SYSTEM) ──────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
def contact_view(request):
    """
    Public support channel (NO LOGIN REQUIRED)

    GET  → render contact form
    POST → submit support message:
           1. Validate input
           2. Save to DB
           3. Send auto-reply email
           4. Notify admin
           Returns JSON response
    """

    # ─────────────────────────────────────────────
    # POST REQUEST
    # ─────────────────────────────────────────────
    if request.method == 'POST':
        try:
            name    = request.POST.get('name', '').strip()
            email   = request.POST.get('email', '').strip()
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()

            # ── VALIDATION ─────────────────────────
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)

            if not email or '@' not in email:
                return JsonResponse({'success': False, 'error': 'Valid email is required.'}, status=400)

            if not message:
                return JsonResponse({'success': False, 'error': 'Message cannot be empty.'}, status=400)

            # ── SAFE IP HANDLING ───────────────────
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip_address:
                ip_address = ip_address.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR', '')

            # ── SAVE TO DATABASE ───────────────────
            contact = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject or 'Support Request',
                message=message,
                ip_address=ip_address,
            )

            # Safe logging (no crash if user is anonymous)
            user_identity = request.user.email if request.user.is_authenticated else email
            logger.info(f'[CONTACT] #{contact.pk} from {user_identity}')

            # ─────────────────────────────────────────────
            # AUTO-REPLY EMAIL
            # ─────────────────────────────────────────────
            try:
                send_mail(
                    subject='We received your message ✔',
                    message=(
                        f'Hi {name},\n\n'
                        f'Thank you for contacting support.\n\n'
                        f'We will respond within 24 hours.\n\n'
                        f'Ticket ID: #BRK-{contact.pk}\n\n'
                        f'Message preview:\n{message[:300]}\n\n'
                        f'— Support Team'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.warning(f'[AUTO-REPLY FAILED] {e}')

            # ─────────────────────────────────────────────
            # ADMIN NOTIFICATION
            # ─────────────────────────────────────────────
            admin_email = getattr(settings, 'CONTACT_ADMIN_EMAIL', '')

            if admin_email:
                try:
                    send_mail(
                        subject=f'[Support Ticket #{contact.pk}] {subject or "New Message"}',
                        message=(
                            f'Name: {name}\n'
                            f'Email: {email}\n'
                            f'Subject: {subject or "No Subject"}\n'
                            f'IP: {ip_address}\n'
                            f'Ticket: #BRK-{contact.pk}\n\n'
                            f'{message}'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin_email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.warning(f'[ADMIN EMAIL FAILED] {e}')

            return JsonResponse({
                'success': True,
                'ticket': f'#BRK-{contact.pk}'
            })

        except Exception as e:
            logger.error(f'[CONTACT ERROR] {e}')
            return JsonResponse({
                'success': False,
                'error': 'Server error. Please try again later.'
            }, status=500)

    # ─────────────────────────────────────────────
    # GET REQUEST
    # ─────────────────────────────────────────────
    whatsapp_number = getattr(settings, 'WHATSAPP_NUMBER', '')

    whatsapp_url = (
        f'https://wa.me/{whatsapp_number}'
        f'?text=Hello%20Support%2C%20I%20need%20help'
        if whatsapp_number else '#'
    )

    return render(request, 'public/contact.html', {
        'whatsapp_url': whatsapp_url,
        'whatsapp_number': whatsapp_number,
    })