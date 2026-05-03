from django.contrib import admin
from .models import LedgerEntry


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'wallet', 'entry_type', 'category', 'amount', 'is_reversed', 'created_at']
    list_filter = ['entry_type', 'category', 'is_reversed']
    search_fields = ['wallet__wallet_id', 'wallet__user__email', 'reference', 'description']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False  # Ledger entries only through service

    def has_change_permission(self, request, obj=None):
        return False  # Immutable audit log

    def has_delete_permission(self, request, obj=None):
        return False  # Never delete ledger entries
