from django.contrib import admin
from django.utils import timezone
from .models import KYCProfile


@admin.register(KYCProfile)
class KYCProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_legal_name', 'document_type', 'status', 'submitted_at', 'reviewed_at']
    list_filter = ['status', 'document_type']
    search_fields = ['user__email', 'full_legal_name', 'document_number']
    readonly_fields = ['id', 'submitted_at', 'updated_at']
    actions = ['approve_kyc', 'reject_kyc']

    fieldsets = (
        ('User', {'fields': ('id', 'user', 'status')}),
        ('Personal Info', {'fields': ('full_legal_name', 'date_of_birth', 'nationality', 'address')}),
        ('Documents', {'fields': ('document_type', 'document_number', 'document_front', 'document_back', 'selfie_with_doc')}),
        ('Review', {'fields': ('rejection_reason', 'reviewed_by', 'reviewed_at')}),
        ('Timestamps', {'fields': ('submitted_at', 'updated_at')}),
    )

    def approve_kyc(self, request, queryset):
        count = 0
        for kyc in queryset.filter(status='PENDING'):
            kyc.status = 'APPROVED'
            kyc.reviewed_by = request.user
            kyc.reviewed_at = timezone.now()
            kyc.save()
            count += 1
        self.message_user(request, f"{count} KYC profile(s) approved.")
    approve_kyc.short_description = "✅ Approve selected KYC"

    def reject_kyc(self, request, queryset):
        count = 0
        for kyc in queryset.filter(status='PENDING'):
            kyc.status = 'REJECTED'
            kyc.reviewed_by = request.user
            kyc.reviewed_at = timezone.now()
            kyc.rejection_reason = 'Rejected via bulk action'
            kyc.save()
            count += 1
        self.message_user(request, f"{count} KYC profile(s) rejected.")
    reject_kyc.short_description = "❌ Reject selected KYC"
