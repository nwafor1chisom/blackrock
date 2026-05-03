from django.contrib import admin
from .models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['wallet_id', 'user', 'balance', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['wallet_id', 'user__email']
    readonly_fields = ['id', 'wallet_id', 'balance', 'profit_balance', 'referral_balance', 'created_at', 'updated_at']

    def balance(self, obj):
        return f"${obj.balance:.2f}"

    def profit_balance(self, obj):
        return f"${obj.profit_balance:.2f}"

    def referral_balance(self, obj):
        return f"${obj.referral_balance:.2f}"
