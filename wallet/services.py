from .models import Wallet


class WalletService:

    @staticmethod
    def create_wallet(user):
        """Create a wallet for a new user. Called once at registration."""
        if hasattr(user, 'wallet'):
            return user.wallet
        return Wallet.objects.create(user=user)

    @staticmethod
    def get_wallet(user):
        """Get or create wallet for user."""
        wallet, created = Wallet.objects.get_or_create(user=user)
        return wallet

    @staticmethod
    def get_balance(user):
        wallet = WalletService.get_wallet(user)
        return wallet.balance

    @staticmethod
    def get_profit_balance(user):
        wallet = WalletService.get_wallet(user)
        return wallet.profit_balance

    @staticmethod
    def get_referral_balance(user):
        wallet = WalletService.get_wallet(user)
        return wallet.referral_balance
