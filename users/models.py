from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib
import secrets as _secrets


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='referrals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)

    def _generate_referral_code(self):
        import random, string
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=8))
            if not User.objects.filter(referral_code=code).exists():
                return code

    @property
    def full_name(self):
        return self.get_full_name()

    @property
    def kyc_status(self):
        try:
            return self.kyc_profile.status
        except Exception:
            return 'NOT_SUBMITTED'

    @property
    def kyc_approved(self):
        return self.kyc_status == 'APPROVED'



# ── OTP Delivery Attempt Log ───────────────────────────────────────────────

class OTPDeliveryLog(models.Model):
    """
    Immutable log of every OTP delivery attempt.
    Used for debugging, auditing, and diagnosing delivery failures.
    """
    CHANNEL_CHOICES = [('EMAIL', 'Email'), ('SMS', 'SMS')]
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED',  'Failed'),
        ('RETRY',   'Retry Attempt'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='otp_delivery_logs'
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='EMAIL')
    recipient = models.CharField(max_length=255)          # email address or phone
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    attempt_number = models.PositiveSmallIntegerField(default=1)
    error_message = models.TextField(blank=True)
    provider = models.CharField(max_length=50, blank=True) # e.g. 'smtp', 'sendgrid'
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'users'
        db_table = 'otp_delivery_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.status}] {self.channel}→{self.recipient} attempt={self.attempt_number}"


# ── Password Reset OTP ─────────────────────────────────────────────────────

class PasswordResetOTP(models.Model):
    """
    Enterprise-grade OTP for password reset.

    Security:
    - SHA-256 hashed — plaintext never persisted
    - Single-use enforced (is_used flag)
    - Hard expiry (OTP_EXPIRY_MINUTES)
    - Rate-limited requests (OTP_MAX_REQUESTS per window)
    - Max verification attempts (OTP_MAX_VERIFY_ATTEMPTS)
    - Constant-time comparison (secrets.compare_digest)
    - Invalidates all previous OTPs on new request

    Delivery:
    - Retry-capable via OTPEmailService (up to MAX_SEND_RETRIES)
    - All send attempts logged in OTPDeliveryLog
    - Debug mode prints OTP to console even if email fails
    """

    OTP_EXPIRY_MINUTES     = 10   # OTP lifetime (reduced from 20 for security)
    OTP_MAX_REQUESTS       = 5    # Max new-OTP requests per rate window
    OTP_RATE_WINDOW_MINUTES = 60  # Rate limit window
    OTP_MAX_VERIFY_ATTEMPTS = 5   # Brute-force guard: max wrong tries
    OTP_RESEND_COOLDOWN_SEC = 60  # Minimum seconds between resend requests

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_otps'
    )
    otp_hash = models.CharField(max_length=64, help_text="SHA-256 hash only.")
    reset_token = models.UUIDField(default=uuid.uuid4, unique=True)

    # State flags
    is_used        = models.BooleanField(default=False)
    is_invalidated = models.BooleanField(default=False)

    # Brute-force guard
    verify_attempts = models.PositiveSmallIntegerField(default=0)

    # Delivery tracking
    delivery_status = models.CharField(
        max_length=20, default='PENDING',
        choices=[
            ('PENDING',  'Pending'),
            ('SENT',     'Sent'),
            ('FAILED',   'Failed'),
            ('RETRYING', 'Retrying'),
        ]
    )
    send_attempts = models.PositiveSmallIntegerField(default=0)
    last_sent_at  = models.DateTimeField(null=True, blank=True)

    # Metadata
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at  = models.DateTimeField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'users'
        db_table  = 'password_reset_otps'
        ordering  = ['-created_at']
        indexes   = [
            models.Index(fields=['user', 'is_used', 'is_invalidated']),
            models.Index(fields=['reset_token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"OTP({self.user.email}) status={self.delivery_status} used={self.is_used}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        super().save(*args, **kwargs)

    # ── Static helpers ─────────────────────────────────────────────────────

    @staticmethod
    def hash_otp(otp_plaintext):
        return hashlib.sha256(otp_plaintext.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_otp():
        """CSPRNG 6-digit OTP — never uses random.randint."""
        return str(_secrets.randbelow(900000) + 100000)

    @classmethod
    def check_rate_limit(cls, user):
        """Returns (allowed: bool, wait_seconds: int)."""
        window_start = timezone.now() - timedelta(minutes=cls.OTP_RATE_WINDOW_MINUTES)
        count = cls.objects.filter(user=user, created_at__gte=window_start).count()
        if count >= cls.OTP_MAX_REQUESTS:
            oldest = (cls.objects
                      .filter(user=user, created_at__gte=window_start)
                      .order_by('created_at').first())
            if oldest:
                reset_at  = oldest.created_at + timedelta(minutes=cls.OTP_RATE_WINDOW_MINUTES)
                wait_secs = max(0, int((reset_at - timezone.now()).total_seconds()))
            else:
                wait_secs = cls.OTP_RATE_WINDOW_MINUTES * 60
            return False, wait_secs
        return True, 0

    @classmethod
    def check_resend_cooldown(cls, user):
        """Returns (can_resend: bool, wait_seconds: int)."""
        latest = (cls.objects
                  .filter(user=user, delivery_status__in=['SENT', 'PENDING', 'RETRYING'],
                          is_used=False, is_invalidated=False)
                  .order_by('-created_at').first())
        if not latest or not latest.last_sent_at:
            return True, 0
        elapsed = (timezone.now() - latest.last_sent_at).total_seconds()
        if elapsed < cls.OTP_RESEND_COOLDOWN_SEC:
            return False, int(cls.OTP_RESEND_COOLDOWN_SEC - elapsed)
        return True, 0

    @classmethod
    def invalidate_previous(cls, user):
        cls.objects.filter(
            user=user, is_used=False, is_invalidated=False
        ).update(is_invalidated=True)

    @classmethod
    def create_for_user(cls, user, ip_address=None, user_agent=''):
        """Invalidate old OTPs and create a new one. Returns (instance, plaintext)."""
        cls.invalidate_previous(user)
        otp_plain = cls.generate_otp()
        instance  = cls.objects.create(
            user=user,
            otp_hash=cls.hash_otp(otp_plain),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return instance, otp_plain

    # ── Instance helpers ───────────────────────────────────────────────────

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def minutes_remaining(self):
        if self.is_expired:
            return 0
        return max(0, int((self.expires_at - timezone.now()).total_seconds() // 60))

    @property
    def seconds_remaining(self):
        if self.is_expired:
            return 0
        return max(0, int((self.expires_at - timezone.now()).total_seconds()))

    @property
    def attempts_remaining(self):
        return max(0, self.OTP_MAX_VERIFY_ATTEMPTS - self.verify_attempts)

    def verify(self, otp_plaintext):
        """
        Constant-time OTP verification with brute-force guard.
        Returns (success: bool, error_code: str).
        error_code: 'USED' | 'INVALIDATED' | 'EXPIRED' | 'MAX_ATTEMPTS' | 'INVALID' | None
        """
        if self.is_used:
            return False, 'USED'
        if self.is_invalidated:
            return False, 'INVALIDATED'
        if self.is_expired:
            return False, 'EXPIRED'
        if self.verify_attempts >= self.OTP_MAX_VERIFY_ATTEMPTS:
            return False, 'MAX_ATTEMPTS'

        submitted_hash = self.hash_otp(otp_plaintext)
        is_valid = _secrets.compare_digest(submitted_hash, self.otp_hash)

        # Always increment attempts (even on success, before marking used)
        self.verify_attempts += 1
        update_fields = ['verify_attempts']

        if is_valid:
            self.verified_at = timezone.now()
            update_fields.append('verified_at')

        self.save(update_fields=update_fields)
        return (True, None) if is_valid else (False, 'INVALID')

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])

    def record_send(self, success, error_message='', attempt_number=1, provider=''):
        """Update delivery tracking fields after a send attempt."""
        self.send_attempts  = attempt_number
        self.last_sent_at   = timezone.now()
        self.delivery_status = 'SENT' if success else (
            'RETRYING' if attempt_number < 3 else 'FAILED'
        )
        self.save(update_fields=['send_attempts', 'last_sent_at', 'delivery_status'])
