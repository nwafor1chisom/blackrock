from django import forms
from payments.models import PaymentMethod


class DepositForm(forms.Form):
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'paymentMethodSelect'}),
        empty_label="-- Select Payment Method --"
    )
    amount = forms.DecimalField(
        max_digits=20, decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': 'Amount (USD)', 'min': '1', 'step': '0.01'})
    )
    tx_hash = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Transaction Hash / TX ID (optional)'})
    )
    sender_address = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Your sending wallet address (optional)'})
    )
    payment_proof = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        pm = self.cleaned_data.get('payment_method')
        if pm and amount and amount < pm.minimum_deposit:
            raise forms.ValidationError(f"Minimum deposit for this method is ${pm.minimum_deposit}")
        return amount


class WithdrawalForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=20, decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': 'Amount to withdraw', 'min': '1', 'step': '0.01'})
    )
    withdrawal_address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Your crypto wallet address'})
    )
    withdrawal_network = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Network (e.g. TRC20, ERC20, BTC)'})
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
