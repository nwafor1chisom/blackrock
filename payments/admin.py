from django.contrib import admin
from .models import PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'wallet_address_short', 'is_active', 'minimum_deposit', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name', 'wallet_address']
    list_editable = ['is_active']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Identity', {'fields': ('id', 'name', 'display_name', 'network_label')}),
        ('Wallet', {'fields': ('wallet_address', 'qr_code')}),
        ('Settings', {'fields': ('minimum_deposit', 'is_active', 'instructions')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def wallet_address_short(self, obj):
        addr = obj.wallet_address
        return f"{addr[:10]}...{addr[-6:]}" if len(addr) > 20 else addr
    wallet_address_short.short_description = 'Wallet Address'
