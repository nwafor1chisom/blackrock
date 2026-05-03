"""
OTPEmailService — Production-grade OTP email delivery.

Features:
- Retry mechanism: up to MAX_RETRIES attempts with exponential backoff
- Every attempt logged to OTPDeliveryLog (success AND failure)
- Debug mode: prints OTP to console when DEBUG=True so dev always sees it
- Detailed error classification (SMTP, DNS, timeout, auth, etc.)
- Anti-spam headers (X-Priority, List-Unsubscribe, proper From)
- Both plaintext and HTML multipart email
- Never silently swallows errors — always logs and returns status
"""

import time
import socket
import smtplib
import logging
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('blackrock.otp')


# ── Configuration ──────────────────────────────────────────────────────────

class OTPEmailConfig:
    MAX_RETRIES         = 3          # Total attempts before giving up
    RETRY_DELAYS        = [2, 5, 10] # Seconds between retries (exponential)
    SMTP_TIMEOUT        = 20         # Seconds before SMTP connection times out
    SUBJECT             = "BLACKROCK — Your Password Reset OTP"
    FROM_EMAIL          = getattr(settings, 'DEFAULT_FROM_EMAIL', 'BLACKROCK <supportblackrock@gmail.com>')
    DEBUG_PRINT_OTP     = getattr(settings, 'OTP_DEBUG_PRINT', getattr(settings, 'DEBUG', False))


# ── Main Service ───────────────────────────────────────────────────────────

class OTPEmailService:

    @classmethod
    def send_otp_email(cls, user, otp_plaintext, expires_minutes=10, otp_instance=None, ip_address=None):
        """
        Send OTP email with retry logic.

        Args:
            user:           Django user instance
            otp_plaintext:  The 6-digit OTP string (plaintext, used once here)
            expires_minutes: Minutes until OTP expires (shown in email)
            otp_instance:   PasswordResetOTP instance for delivery tracking
            ip_address:     Requester's IP for audit log

        Returns:
            dict: {
                'success': bool,
                'attempts': int,
                'error': str | None,
                'provider': str,
            }
        """
        # ── Debug mode: always print OTP so devs can test without SMTP ──
        if OTPEmailConfig.DEBUG_PRINT_OTP:
            cls._debug_print(user.email, otp_plaintext, expires_minutes)

        result = {
            'success': False,
            'attempts': 0,
            'error': None,
            'provider': cls._detect_provider(),
        }

        last_error = None

        for attempt in range(1, OTPEmailConfig.MAX_RETRIES + 1):
            result['attempts'] = attempt
            logger.info(f"[OTP SEND] user={user.email} attempt={attempt}/{OTPEmailConfig.MAX_RETRIES}")

            try:
                cls._send_single(user, otp_plaintext, expires_minutes)

                # SUCCESS
                result['success'] = True
                result['error']   = None
                logger.info(f"[OTP SENT OK] user={user.email} attempt={attempt}")
                cls._log_delivery(user, 'SUCCESS', '', attempt, result['provider'], ip_address, otp_instance)
                break

            except smtplib.SMTPAuthenticationError as e:
                msg = f"SMTP auth failed — check EMAIL_HOST_USER / EMAIL_HOST_PASSWORD. Detail: {e}"
                logger.error(f"[OTP AUTH ERROR] user={user.email}: {msg}")
                last_error = msg
                cls._log_delivery(user, 'FAILED', msg, attempt, result['provider'], ip_address, otp_instance)
                break  # Auth errors won't resolve with retry

            except smtplib.SMTPRecipientsRefused as e:
                msg = f"Recipient refused: {user.email}. Detail: {e}"
                logger.error(f"[OTP RECIPIENT ERROR] {msg}")
                last_error = msg
                cls._log_delivery(user, 'FAILED', msg, attempt, result['provider'], ip_address, otp_instance)
                break  # Recipient errors won't resolve with retry

            except smtplib.SMTPServerDisconnected as e:
                msg = f"SMTP server disconnected unexpectedly: {e}"
                logger.warning(f"[OTP DISCONNECT] user={user.email} attempt={attempt}: {msg}")
                last_error = msg
                cls._log_delivery(user, 'RETRY', msg, attempt, result['provider'], ip_address, otp_instance)

            except smtplib.SMTPConnectError as e:
                msg = f"Cannot connect to SMTP server (check EMAIL_HOST / EMAIL_PORT): {e}"
                logger.warning(f"[OTP CONNECT ERROR] user={user.email} attempt={attempt}: {msg}")
                last_error = msg
                cls._log_delivery(user, 'RETRY', msg, attempt, result['provider'], ip_address, otp_instance)

            except socket.timeout:
                msg = f"SMTP connection timed out after {OTPEmailConfig.SMTP_TIMEOUT}s"
                logger.warning(f"[OTP TIMEOUT] user={user.email} attempt={attempt}: {msg}")
                last_error = msg
                cls._log_delivery(user, 'RETRY', msg, attempt, result['provider'], ip_address, otp_instance)

            except socket.gaierror as e:
                msg = f"DNS resolution failed for EMAIL_HOST: {e}"
                logger.error(f"[OTP DNS ERROR] user={user.email}: {msg}")
                last_error = msg
                cls._log_delivery(user, 'FAILED', msg, attempt, result['provider'], ip_address, otp_instance)
                break  # DNS failure won't resolve with retry

            except Exception as e:
                msg = f"{type(e).__name__}: {e}"
                logger.error(f"[OTP UNEXPECTED ERROR] user={user.email} attempt={attempt}: {msg}")
                last_error = msg
                cls._log_delivery(user, 'RETRY', msg, attempt, result['provider'], ip_address, otp_instance)

            # Wait before next retry (skip wait after last attempt)
            if attempt < OTPEmailConfig.MAX_RETRIES:
                delay = OTPEmailConfig.RETRY_DELAYS[min(attempt - 1, len(OTPEmailConfig.RETRY_DELAYS) - 1)]
                logger.info(f"[OTP RETRY WAIT] {delay}s before attempt {attempt + 1}")
                time.sleep(delay)

        if not result['success']:
            result['error'] = last_error or "Unknown email delivery error"
            logger.error(
                f"[OTP DELIVERY FAILED] user={user.email} after {result['attempts']} attempt(s). "
                f"Error: {result['error']}"
            )
            if otp_instance:
                otp_instance.record_send(False, result['error'], result['attempts'], result['provider'])

        elif otp_instance:
            otp_instance.record_send(True, '', result['attempts'], result['provider'])

        return result

    # ── Internal send ──────────────────────────────────────────────────────

    @classmethod
    def _send_single(cls, user, otp_plaintext, expires_minutes):
        """Execute a single send attempt. Raises on any failure."""
        text_body = cls._build_text(user, otp_plaintext, expires_minutes)
        html_body = cls._build_html(user, otp_plaintext, expires_minutes)

        msg = EmailMultiAlternatives(
            subject=OTPEmailConfig.SUBJECT,
            body=text_body,
            from_email=OTPEmailConfig.FROM_EMAIL,
            to=[user.email],
            headers={
                'X-Priority':         '1',
                'X-Mailer':           'BLACKROCK OTP System',
                'X-OTP-Request':      'password-reset',
                'Precedence':         'transactional',
                'Auto-Submitted':     'auto-generated',
                'List-Unsubscribe':   '<mailto:unsubscribe@blackrock.com>',
            }
        )
        msg.attach_alternative(html_body, "text/html")
        # Use a fresh connection per attempt so stale connections don't cause failures
        connection = get_connection(timeout=OTPEmailConfig.SMTP_TIMEOUT)
        msg.connection = connection
        msg.send(fail_silently=False)

    # ── Delivery log helper ────────────────────────────────────────────────

    @staticmethod
    def _log_delivery(user, status, error_message, attempt, provider, ip_address, otp_instance):
        """Write a row to OTPDeliveryLog for every attempt."""
        try:
            from users.models import OTPDeliveryLog
            OTPDeliveryLog.objects.create(
                user=user,
                channel='EMAIL',
                recipient=user.email,
                status=status,
                attempt_number=attempt,
                error_message=error_message,
                provider=provider,
                ip_address=ip_address,
            )
        except Exception as log_err:
            logger.error(f"[OTP LOG ERROR] Could not write delivery log: {log_err}")

    # ── Provider detection ─────────────────────────────────────────────────

    @staticmethod
    def _detect_provider():
        """Identify which email backend is configured."""
        backend = getattr(settings, 'EMAIL_BACKEND', '')
        if 'console' in backend:
            return 'console'
        if 'smtp' in backend.lower():
            host = getattr(settings, 'EMAIL_HOST', '')
            if 'sendgrid' in host:
                return 'sendgrid'
            if 'mailgun' in host:
                return 'mailgun'
            if 'ses' in host or 'amazonaws' in host:
                return 'aws-ses'
            if 'gmail' in host:
                return 'gmail-smtp'
            if 'outlook' in host or 'office365' in host:
                return 'outlook-smtp'
            return 'smtp'
        if 'dummy' in backend:
            return 'dummy'
        return 'custom'

    # ── Debug helper ───────────────────────────────────────────────────────

    @staticmethod
    def _debug_print(email, otp, expires_minutes):
        """Print OTP to console/terminal so developers can always see it."""
        separator = '─' * 56
        print(f"\n{separator}")
        print(f"  🔑 BLACKROCK OTP DEBUG")
        print(f"{separator}")
        print(f"  Email:   {email}")
        print(f"  OTP:     {otp}")
        print(f"  Expires: {expires_minutes} minutes from now")
        print(f"  Time:    {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{separator}\n")
        logger.debug(f"[OTP DEBUG] email={email} otp={otp} expires_in={expires_minutes}m")

    # ── Email content builders ─────────────────────────────────────────────

    @staticmethod
    def _build_text(user, otp, expires_minutes):
        name = user.get_full_name() or user.email
        return (
            f"BLACKROCK — Password Reset OTP\n"
            f"{'=' * 40}\n\n"
            f"Hello {name},\n\n"
            f"Your one-time password (OTP) for resetting your BLACKROCK account password is:\n\n"
            f"  {otp}\n\n"
            f"This OTP expires in {expires_minutes} minutes.\n\n"
            f"If you did not request this, ignore this email — your password is unchanged.\n\n"
            f"Do NOT share this code with anyone.\n"
            f"BLACKROCK staff will NEVER ask for your OTP.\n\n"
            f"— BLACKROCK Security Team\n"
            f"  https://blackrock.com\n"
        )

    @staticmethod
    def _build_html(user, otp, expires_minutes):
        name = user.get_full_name() or user.email
        digit_cells = ''.join(
            f'<td style="padding:0 4px;">'
            f'<div style="width:48px;height:60px;line-height:60px;text-align:center;'
            f'background:#16161a;border:2px solid #c9a84c;border-radius:10px;'
            f'font-family:Courier New,monospace;font-size:28px;font-weight:700;color:#c9a84c;">'
            f'{d}</div></td>'
            for d in otp
        )
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <title>BLACKROCK OTP</title>
</head>
<body style="margin:0;padding:0;background:#0a0a0b;font-family:Arial,Helvetica,sans-serif;-webkit-font-smoothing:antialiased;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0a0a0b;padding:32px 16px;">
<tr><td align="center">
<table width="580" cellpadding="0" cellspacing="0" border="0" style="max-width:580px;background:#111114;border:1px solid #2a2410;border-radius:12px;overflow:hidden;">

  <!-- HEADER -->
  <tr>
    <td style="background:#0f0f12;padding:28px 40px;border-bottom:1px solid #2a2410;text-align:center;">
      <table cellpadding="0" cellspacing="0" border="0" align="center">
        <tr>
          <td style="background:linear-gradient(135deg,#c9a84c,#9a7a30);width:38px;height:38px;border-radius:8px;text-align:center;vertical-align:middle;">
            <span style="font-size:20px;color:#000;font-weight:900;">&#9830;</span>
          </td>
          <td style="padding-left:10px;font-family:Georgia,serif;font-size:20px;font-weight:700;letter-spacing:3px;color:#c9a84c;vertical-align:middle;">
            BLACKROCK
          </td>
        </tr>
      </table>
      <p style="margin:8px 0 0;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#4a4540;">
        Digital Finance Platform
      </p>
    </td>
  </tr>

  <!-- BODY -->
  <tr>
    <td style="padding:40px;">

      <h1 style="font-family:Georgia,serif;font-size:22px;font-weight:600;color:#f0ece4;margin:0 0 10px;">
        Password Reset Request
      </h1>
      <p style="font-size:14px;color:#a89f93;margin:0 0 28px;line-height:1.7;">
        Hello <strong style="color:#f0ece4;">{name}</strong>,<br>
        Enter the following OTP to reset your BLACKROCK password.
      </p>

      <!-- OTP DIGITS -->
      <div style="background:#0d0d10;border:1px solid #2a2410;border-radius:10px;padding:28px;text-align:center;margin:0 0 24px;">
        <p style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#4a4540;margin:0 0 18px;">
          Your One-Time Password
        </p>
        <table cellpadding="0" cellspacing="0" border="0" align="center">
          <tr>{digit_cells}</tr>
        </table>
        <p style="font-size:12px;color:#c9a84c;margin:16px 0 0;">
          Expires in <strong>{expires_minutes} minutes</strong>
        </p>
      </div>

      <!-- WARNING BOX -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#1a1400;border:1px solid #3a2e00;border-radius:8px;margin-bottom:24px;">
        <tr>
          <td style="padding:14px 18px;">
            <table cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="font-size:18px;color:#f0a500;vertical-align:top;padding-right:10px;">&#9888;</td>
                <td>
                  <p style="font-size:13px;font-weight:600;color:#f0a500;margin:0 0 4px;">
                    Security Notice
                  </p>
                  <p style="font-size:12px;color:#a89f93;margin:0;line-height:1.6;">
                    This OTP is valid once only. If you did not request this, please ignore this email.
                    <strong>BLACKROCK staff will NEVER ask for your OTP.</strong>
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- TIPS -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#16161a;border-radius:8px;">
        <tr>
          <td style="padding:16px 20px;">
            <p style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#4a4540;margin:0 0 10px;">
              Tips if you didn't receive this email
            </p>
            <ul style="margin:0;padding:0 0 0 16px;font-size:12px;color:#7a7570;line-height:2.2;">
              <li>Check your spam / junk folder</li>
              <li>Add supportblackrock@gmail.com to your contacts</li>
              <li>Wait 1–2 minutes and request again if needed</li>
              <li>Make sure you used the correct email address</li>
            </ul>
          </td>
        </tr>
      </table>

    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#0f0f12;padding:18px 40px;border-top:1px solid #1a1a1f;text-align:center;">
      <p style="font-size:11px;color:#3a3530;margin:0;">
        &copy; 2025 BLACKROCK Digital Finance &nbsp;|&nbsp; SECURE &nbsp;|&nbsp; ENCRYPTED &nbsp;|&nbsp; AUDITED
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""
