from django.db import models
from django.conf import settings
import uuid
from cloudinary.models import CloudinaryField


class KYCProfile(models.Model):
    STATUS_CHOICES = [
        ('NOT_SUBMITTED', 'Not Submitted'),
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    DOC_TYPE_CHOICES = [
        ('PASSPORT', 'Passport'),
        ('NATIONAL_ID', 'National ID'),
        ('DRIVERS_LICENSE', "Driver's License"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kyc_profile'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_SUBMITTED')

    # Personal info
    full_legal_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=100)
    address = models.TextField()

    # Document
    document_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    document_number = models.CharField(max_length=100)
    document_front = CloudinaryField('image', folder='kyc_docs/front')
    document_back = CloudinaryField('image', folder='kyc_docs/back', blank=True, null=True)
    selfie_with_doc = CloudinaryField('image', folder='kyc_docs/selfie', blank=True, null=True)

    # Admin review
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='kyc_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kyc_profiles'

    def __str__(self):
        return f"KYC({self.user.email}) - {self.status}"