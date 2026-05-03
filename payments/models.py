from django.db import models
import uuid


class PaymentMethod(models.Model):
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin (BTC)'),
        ('ETH', 'Ethereum (ETH)'),
        ('USDT_TRC20', 'USDT (TRC20)'),
        ('USDT_ERC20', 'USDT (ERC20)'),
        ('USDT_BEP20', 'USDT (BEP20)'),
        ('USDC', 'USD Coin (USDC)'),
        ('BNB', 'Binance Coin (BNB)'),
        ('TRX', 'TRON (TRX)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20, choices=CRYPTO_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    wallet_address = models.CharField(max_length=255)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    network_label = models.CharField(max_length=100, blank=True, help_text='e.g. TRC20, ERC20')
    minimum_deposit = models.DecimalField(max_digits=20, decimal_places=8, default=10)
    is_active = models.BooleanField(default=True)
    instructions = models.TextField(blank=True, help_text='Special deposit instructions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_methods'
        ordering = ['name']

    def __str__(self):
        return f"{self.display_name} ({self.wallet_address[:12]}...)"
