from django.contrib import admin
from django.utils.html import format_html
from .models import AuditLog, InvestmentPlan, ContactMessage


# ── Investment Plans ───────────────────────────────────────────────────────

@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display  = ('name', 'interest_badge', 'duration', 'range_display',
                     'is_active', 'sort_order', 'created_at')
    list_filter   = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'sort_order')
    ordering      = ('sort_order', 'min_amount')

    fieldsets = (
        ('Plan Identity', {
            'fields': ('name', 'description', 'sort_order', 'is_active')
        }),
        ('Financial Details', {
            'fields': ('interest', 'duration')
        }),
        ('Investment Range', {
            'fields': ('min_amount', 'max_amount'),
            'description': 'Leave max_amount blank for Unlimited'
        }),
    )

    def interest_badge(self, obj):
        return format_html(
            '<strong style="color:#c9a84c; font-size:14px;">{:.1f}%</strong>', obj.interest
        )
    interest_badge.short_description = 'Return %'

    def range_display(self, obj):
        max_str = f'${obj.max_amount:,.2f}' if obj.max_amount else 'Unlimited'
        return f'${obj.min_amount:,.2f} — {max_str}'
    range_display.short_description = 'Range'


# ── Contact Messages ───────────────────────────────────────────────────────

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'subject_display', 'is_read', 'ip_address', 'created_at')
    list_filter   = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    ordering      = ('-created_at',)
    list_editable = ('is_read',)
    readonly_fields = ('name', 'email', 'subject', 'message', 'ip_address', 'created_at')
    actions       = ['mark_as_read', 'mark_as_unread']

    fieldsets = (
        ('Sender Info',   {'fields': ('name', 'email', 'ip_address', 'created_at')}),
        ('Message',       {'fields': ('subject', 'message')}),
        ('Admin',         {'fields': ('is_read',)}),
    )

    def subject_display(self, obj):
        return obj.subject or '— No Subject —'
    subject_display.short_description = 'Subject'

    def mark_as_read(self, request, queryset):
        n = queryset.update(is_read=True)
        self.message_user(request, f'{n} message(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        n = queryset.update(is_read=False)
        self.message_user(request, f'{n} message(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'

    def has_add_permission(self, request):
        return False  # Only created via form submission


# ── Audit Log ──────────────────────────────────────────────────────────────

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('action', 'user', 'ip_address', 'created_at')
    list_filter   = ('action', 'created_at')
    search_fields = ('user__email', 'description', 'ip_address')
    readonly_fields = ('id', 'user', 'action', 'description', 'ip_address',
                       'user_agent', 'extra_data', 'created_at')
    ordering      = ('-created_at',)

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
