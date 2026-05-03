from django.db import models
from django.conf import settings
import uuid


class ReferralBonus(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_bonuses_earned'
    )
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_caused'
    )
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    note = models.TextField(blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='referral_approvals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'referral_bonuses'
        ordering = ['-created_at']

    def __str__(self):
        return f"Referral bonus {self.amount} to {self.referrer.email} - {self.status}"
