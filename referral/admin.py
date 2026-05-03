from django.contrib import admin
from django.utils.html import format_html
from .models import ReferralBonus
from .services import ReferralService


@admin.register(ReferralBonus)
class ReferralBonusAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_user', 'amount', 'status_badge', 'approved_by', 'created_at']
    list_filter = ['status']
    search_fields = ['referrer__email', 'referred_user__email']
    readonly_fields = ['id', 'created_at', 'approved_by', 'approved_at']
    ordering = ['-created_at']
    actions = ['approve_bonuses', 'reject_bonuses']

    fieldsets = (
        ('Referral Info', {'fields': ('id', 'referrer', 'referred_user', 'amount', 'status', 'note')}),
        ('Approval', {'fields': ('approved_by', 'approved_at')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

    def status_badge(self, obj):
        colors = {
            'PENDING': '#f59e0b',
            'APPROVED': '#10b981',
            'REJECTED': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'

    def approve_bonuses(self, request, queryset):
        count = 0
        for bonus in queryset.filter(status='PENDING'):
            try:
                ReferralService.approve_referral_bonus(bonus, request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error: {e}", level='error')
        self.message_user(request, f"{count} referral bonus(es) approved and credited.")
    approve_bonuses.short_description = "Approve selected referral bonuses"

    def reject_bonuses(self, request, queryset):
        count = 0
        for bonus in queryset.filter(status='PENDING'):
            try:
                ReferralService.reject_referral_bonus(bonus, request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error: {e}", level='error')
        self.message_user(request, f"{count} referral bonus(es) rejected.")
    reject_bonuses.short_description = "Reject selected referral bonuses"
