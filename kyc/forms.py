from django import forms
from .models import KYCProfile


class KYCSubmitForm(forms.ModelForm):
    class Meta:
        model = KYCProfile
        fields = [
            'full_legal_name', 'date_of_birth', 'nationality', 'address',
            'document_type', 'document_number',
            'document_front', 'document_back', 'selfie_with_doc'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Full residential address'}),
            'full_legal_name': forms.TextInput(attrs={'placeholder': 'Full legal name as on document'}),
            'document_number': forms.TextInput(attrs={'placeholder': 'Document ID number'}),
            'nationality': forms.TextInput(attrs={'placeholder': 'Your nationality'}),
        }
