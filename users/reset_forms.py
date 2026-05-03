from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your registered email address',
            'autocomplete': 'email',
        }),
        label='Email Address',
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        # Security: do NOT reveal whether email exists at form level.
        # The view handles that with a generic response.
        return email


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '000000',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'style': 'text-align:center;letter-spacing:0.4em;font-size:22px;',
        }),
        label='One-Time Password',
    )

    def clean_otp(self):
        otp = self.cleaned_data.get('otp', '').strip()
        if not otp.isdigit():
            raise forms.ValidationError("OTP must contain digits only.")
        if len(otp) != 6:
            raise forms.ValidationError("OTP must be exactly 6 digits.")
        return otp


class SetNewPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'New password', 'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password', 'autocomplete': 'new-password'}),
    )

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned
