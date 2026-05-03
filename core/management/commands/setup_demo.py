"""
python manage.py setup_demo

Creates:
  - Admin account
  - Demo user account
  - 6 investment plans (if none exist)
  - 7 crypto payment methods (if none exist)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up demo data: admin, demo user, plans, payment methods'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== BlackRock Demo Setup ===\n'))

        # ── Admin ──
        if not User.objects.filter(email='admin@blackrock.com').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@blackrock.com',
                password='Admin@1234',
                first_name='Platform',
                last_name='Admin',
            )
            from wallet.services import WalletService
            WalletService.create_wallet(admin)
            self.stdout.write(self.style.SUCCESS('Admin: admin@blackrock.com / Admin@1234'))
        else:
            self.stdout.write(self.style.WARNING('Admin already exists'))

        # ── Demo user ──
        if not User.objects.filter(email='demo@blackrock.com').exists():
            user = User.objects.create_user(
                username='demouser',
                email='demo@blackrock.com',
                password='Demo@1234',
                first_name='Demo',
                last_name='User',
            )
            from wallet.services import WalletService
            WalletService.create_wallet(user)
            self.stdout.write(self.style.SUCCESS('Demo user: demo@blackrock.com / Demo@1234'))
        else:
            self.stdout.write(self.style.WARNING('Demo user already exists'))

        # ── Investment plans ──
        from core.models import InvestmentPlan
        if not InvestmentPlan.objects.exists():
            plans = [
                {'name': 'Starter Plan',  'interest': 6.0,  'duration': '24 hrs',  'min_amount': 100,    'max_amount': 999,    'sort_order': 1},
                {'name': 'Basic Plan',    'interest': 10.0, 'duration': '48 hrs',  'min_amount': 1000,   'max_amount': 4999,   'sort_order': 2},
                {'name': 'Advanced Plan', 'interest': 15.0, 'duration': '7 Days',  'min_amount': 5000,   'max_amount': 19999,  'sort_order': 3},
                {'name': 'Premium Plan',  'interest': 20.0, 'duration': '14 Days', 'min_amount': 20000,  'max_amount': 49999,  'sort_order': 4},
                {'name': 'Elite Plan',    'interest': 25.0, 'duration': '21 Days', 'min_amount': 50000,  'max_amount': 99999,  'sort_order': 5},
                {'name': 'VIP Plan',      'interest': 30.0, 'duration': '30 Days', 'min_amount': 100000, 'max_amount': None,   'sort_order': 6},
            ]
            for p in plans:
                InvestmentPlan.objects.create(**p, is_active=True)
            self.stdout.write(self.style.SUCCESS(f'{len(plans)} investment plans created'))
        else:
            self.stdout.write(self.style.WARNING(f'Plans exist ({InvestmentPlan.objects.count()} found)'))

        # ── Payment methods ──
        from payments.models import PaymentMethod
        methods = [
            {'name': 'BTC',        'display_name': 'Bitcoin (BTC)',      'wallet_address': '1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf8N',           'network_label': 'Bitcoin Network', 'minimum_deposit': 10},
            {'name': 'ETH',        'display_name': 'Ethereum (ETH)',     'wallet_address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',    'network_label': 'ERC20',           'minimum_deposit': 10},
            {'name': 'USDT_TRC20', 'display_name': 'USDT (TRC20)',       'wallet_address': 'TJCnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW',           'network_label': 'TRC20',           'minimum_deposit': 10},
            {'name': 'USDT_ERC20', 'display_name': 'USDT (ERC20)',       'wallet_address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',    'network_label': 'ERC20',           'minimum_deposit': 10},
            {'name': 'USDC',       'display_name': 'USD Coin (USDC)',    'wallet_address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',    'network_label': 'ERC20',           'minimum_deposit': 10},
            {'name': 'BNB',        'display_name': 'Binance Coin (BNB)', 'wallet_address': 'bnb1grpf0955h0ykzq3ar5nmum7y6gdfl6lxfn46h2',   'network_label': 'BEP20',           'minimum_deposit': 10},
            {'name': 'TRX',        'display_name': 'TRON (TRX)',         'wallet_address': 'TJCnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW',           'network_label': 'TRC20',           'minimum_deposit': 10},
        ]
        created = 0
        for m in methods:
            _, was_created = PaymentMethod.objects.get_or_create(name=m['name'], defaults={**m, 'is_active': True})
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'{created} payment method(s) created'))

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Setup Complete ==='))
        self.stdout.write('')
        self.stdout.write('  Home:          http://127.0.0.1:8000/')
        self.stdout.write('  Plans:         http://127.0.0.1:8000/plan/')
        self.stdout.write('  Contact:       http://127.0.0.1:8000/contact/')
        self.stdout.write('  Login:         http://127.0.0.1:8000/users/login/')
        self.stdout.write('  Dashboard:     http://127.0.0.1:8000/dashboard/')
        self.stdout.write('  Admin panel:   http://127.0.0.1:8000/admin/')
        self.stdout.write('  Custom admin:  http://127.0.0.1:8000/adminpanel/')
        self.stdout.write('')
        self.stdout.write('  Admin creds:   admin@blackrock.com / Admin@1234')
        self.stdout.write('  Demo creds:    demo@blackrock.com  / Demo@1234')
        self.stdout.write('')
