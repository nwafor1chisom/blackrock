from django.db import models
from django.conf import settings
import uuid


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('DEPOSIT_SUBMIT', 'Deposit Submitted'),
        ('DEPOSIT_APPROVE', 'Deposit Approved'),
        ('DEPOSIT_REJECT', 'Deposit Rejected'),
        ('WITHDRAW_SUBMIT', 'Withdrawal Submitted'),
        ('WITHDRAW_APPROVE', 'Withdrawal Approved'),
        ('WITHDRAW_REJECT', 'Withdrawal Rejected'),
        ('KYC_SUBMIT', 'KYC Submitted'),
        ('KYC_APPROVE', 'KYC Approved'),
        ('KYC_REJECT', 'KYC Rejected'),
        ('BONUS_CREDIT', 'Bonus Credited'),
        ('REFERRAL_APPROVE', 'Referral Approved'),
        ('PROFILE_UPDATE', 'Profile Updated'),
        ('ADMIN_ACTION', 'Admin Action'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"[{self.action}] {self.user} — {self.created_at:%Y-%m-%d %H:%M}"

    @classmethod
    def log(cls, action, description, user=None, request=None, extra_data=None):
        ip = None
        ua = ''
        if request:
            forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = forwarded.split(',')[0] if forwarded else request.META.get('REMOTE_ADDR')
            ua = request.META.get('HTTP_USER_AGENT', '')
        return cls.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip,
            user_agent=ua,
            extra_data=extra_data or {},
        )


# ── Investment Plans ───────────────────────────────────────────────────────

class InvestmentPlan(models.Model):
    """
    Public-facing investment plan shown on plan.html.
    Fully database-driven — admin controls all values.
    Connected to the transactions system: users click 'Invest Now'
    which routes to the authenticated deposit flow with the plan pre-selected.
    """
    name       = models.CharField(max_length=100)
    interest   = models.FloatField(help_text="Return percentage, e.g. 6 for 6%")
    duration   = models.CharField(max_length=50, help_text="e.g. '24 hrs', '7 Days', '30 Days'")
    min_amount = models.DecimalField(max_digits=14, decimal_places=2)
    max_amount = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        help_text="Leave blank for Unlimited"
    )
    is_active  = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Lower number displayed first on plan page"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional extra details shown on plan card"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'investment_plans'
        ordering  = ['sort_order', 'min_amount']
        verbose_name = 'Investment Plan'
        verbose_name_plural = 'Investment Plans'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return f"{self.name} — {self.interest}% / {self.duration}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_amount and self.max_amount:
            if self.min_amount > self.max_amount:
                raise ValidationError("min_amount cannot exceed max_amount")
        if self.interest is not None and self.interest < 0:
            raise ValidationError("Interest rate cannot be negative")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# ── Contact Messages ───────────────────────────────────────────────────────

class ContactMessage(models.Model):
    """
    Messages submitted via contact.html form.
    Stored permanently — admin views in /admin/core/contactmessage/.
    Email notification optionally sent to CONTACT_ADMIN_EMAIL setting.
    """
    name    = models.CharField(max_length=255)
    email   = models.EmailField()
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'contact_messages'
        ordering  = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        indexes = [
            models.Index(fields=['is_read']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} — {self.subject or 'No Subject'} ({self.created_at:%Y-%m-%d})"
