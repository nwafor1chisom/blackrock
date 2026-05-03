from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction
from .services import DepositService, WithdrawalService


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'user', 'transaction_type', 'amount', 'status_badge', 'payment_method', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['reference', 'user__email', 'tx_hash', 'withdrawal_address']
    readonly_fields = ['id', 'reference', 'created_at', 'updated_at', 'ip_address']
    ordering = ['-created_at']
    actions = ['approve_deposits', 'reject_deposits', 'approve_withdrawals', 'reject_withdrawals']

    fieldsets = (
        ('Core', {'fields': ('id', 'reference', 'user', 'wallet', 'transaction_type', 'status', 'amount')}),
        ('Deposit Info', {'fields': ('payment_method', 'tx_hash', 'sender_address', 'payment_proof')}),
        ('Withdrawal Info', {'fields': ('withdrawal_address', 'withdrawal_network')}),
        ('Admin Review', {'fields': ('admin_note', 'reviewed_by', 'reviewed_at')}),
        ('Metadata', {'fields': ('ip_address', 'created_at', 'updated_at')}),
    )

    def status_badge(self, obj):
        colors = {
            'PENDING': '#f59e0b',
            'APPROVED': '#10b981',
            'REJECTED': '#ef4444',
            'CANCELLED': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'

    def approve_deposits(self, request, queryset):
        approved = 0
        for txn in queryset.filter(transaction_type='DEPOSIT', status='PENDING'):
            try:
                DepositService.approve_deposit(txn, request.user, note='Bulk approved')
                approved += 1
            except Exception as e:
                self.message_user(request, f"Error approving {txn.reference}: {e}", level='error')
        self.message_user(request, f"{approved} deposit(s) approved.")
    approve_deposits.short_description = "✅ Approve selected deposits"

    def reject_deposits(self, request, queryset):
        rejected = 0
        for txn in queryset.filter(transaction_type='DEPOSIT', status='PENDING'):
            try:
                DepositService.reject_deposit(txn, request.user, note='Bulk rejected')
                rejected += 1
            except Exception as e:
                self.message_user(request, f"Error: {e}", level='error')
        self.message_user(request, f"{rejected} deposit(s) rejected.")
    reject_deposits.short_description = "❌ Reject selected deposits"

    def approve_withdrawals(self, request, queryset):
        approved = 0
        for txn in queryset.filter(transaction_type='WITHDRAWAL', status='PENDING'):
            try:
                WithdrawalService.approve_withdrawal(txn, request.user, note='Bulk approved')
                approved += 1
            except Exception as e:
                self.message_user(request, f"Error: {e}", level='error')
        self.message_user(request, f"{approved} withdrawal(s) approved.")
    approve_withdrawals.short_description = "✅ Approve selected withdrawals"

    def reject_withdrawals(self, request, queryset):
        rejected = 0
        for txn in queryset.filter(transaction_type='WITHDRAWAL', status='PENDING'):
            try:
                WithdrawalService.reject_withdrawal(txn, request.user, note='Bulk rejected')
                rejected += 1
            except Exception as e:
                self.message_user(request, f"Error: {e}", level='error')
        self.message_user(request, f"{rejected} withdrawal(s) rejected.")
    reject_withdrawals.short_description = "❌ Reject selected withdrawals"
