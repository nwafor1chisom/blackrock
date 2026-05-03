from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, PasswordResetOTP, OTPDeliveryLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'full_name', 'kyc_status', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = ['id', 'referral_code', 'created_at', 'updated_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('phone_number', 'date_of_birth', 'country', 'address', 'profile_picture')}),
        ('Referral', {'fields': ('referral_code', 'referred_by')}),
        ('Verification', {'fields': ('is_email_verified',)}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'status_badge', 'delivery_badge', 'send_attempts',
                    'verify_attempts', 'ip_address', 'expires_at', 'created_at']
    list_filter = ['is_used', 'is_invalidated', 'delivery_status']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = [
        'id', 'user', 'otp_hash', 'reset_token',
        'is_used', 'is_invalidated', 'verify_attempts',
        'delivery_status', 'send_attempts', 'last_sent_at',
        'ip_address', 'user_agent', 'verified_at', 'expires_at', 'created_at'
    ]
    ordering = ['-created_at']

    def status_badge(self, obj):
        if obj.is_used:
            color, label = '#10b981', 'USED'
        elif obj.is_invalidated:
            color, label = '#6b7280', 'INVALIDATED'
        elif obj.is_expired:
            color, label = '#ef4444', 'EXPIRED'
        elif obj.verify_attempts >= obj.OTP_MAX_VERIFY_ATTEMPTS:
            color, label = '#ef4444', 'LOCKED'
        else:
            color, label = '#f59e0b', 'ACTIVE'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'OTP Status'

    def delivery_badge(self, obj):
        colors = {'SENT': '#10b981', 'FAILED': '#ef4444', 'RETRYING': '#f59e0b', 'PENDING': '#6b7280'}
        color = colors.get(obj.delivery_status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color, obj.delivery_status
        )
    delivery_badge.short_description = 'Delivery'

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


@admin.register(OTPDeliveryLog)
class OTPDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'channel', 'recipient',
                    'status_badge', 'attempt_number', 'provider', 'error_short']
    list_filter = ['status', 'channel', 'provider', 'created_at']
    search_fields = ['user__email', 'recipient', 'error_message', 'ip_address']
    readonly_fields = ['id', 'user', 'channel', 'recipient', 'status',
                       'attempt_number', 'error_message', 'provider',
                       'ip_address', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def status_badge(self, obj):
        colors = {'SUCCESS': '#10b981', 'FAILED': '#ef4444', 'RETRY': '#f59e0b'}
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'

    def error_short(self, obj):
        if not obj.error_message:
            return format_html('<span style="color:#10b981;">—</span>')
        short = obj.error_message[:60]
        return format_html(
            '<span style="color:#ef4444;font-size:12px;" title="{}">{}</span>',
            obj.error_message, short + ('…' if len(obj.error_message) > 60 else '')
        )
    error_short.short_description = 'Error'

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser
