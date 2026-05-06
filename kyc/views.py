# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from .models import KYCProfile
# from .forms import KYCSubmitForm


# @login_required
# def kyc_submit_view(request):
#     try:
#         kyc = request.user.kyc_profile
#         if kyc.status == 'APPROVED':
#             return redirect('kyc:status')
#         if kyc.status == 'PENDING':
#             messages.info(request, 'Your KYC is currently under review.')
#             return redirect('kyc:status')
#     except KYCProfile.DoesNotExist:
#         kyc = None

#     if request.method == 'POST':
#         if kyc and kyc.status not in ['NOT_SUBMITTED', 'REJECTED']:
#             messages.error(request, 'You cannot resubmit at this stage.')
#             return redirect('kyc:status')

#         form = KYCSubmitForm(request.POST, request.FILES, instance=kyc)
#         if form.is_valid():
#             profile = form.save(commit=False)
#             profile.user = request.user
#             profile.status = 'PENDING'
#             profile.save()
#             messages.success(request, 'KYC documents submitted successfully! Awaiting review.')
#             return redirect('kyc:status')
#     else:
#         form = KYCSubmitForm(instance=kyc)

#     return render(request, 'kyc/submit.html', {'form': form, 'kyc': kyc})


# @login_required
# def kyc_status_view(request):
#     try:
#         kyc = request.user.kyc_profile
#     except KYCProfile.DoesNotExist:
#         kyc = None
#     return render(request, 'kyc/status.html', {'kyc': kyc})


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import KYCProfile
from .forms import KYCSubmitForm
import logging

logger = logging.getLogger(__name__)


@login_required
def kyc_submit_view(request):
    from django.conf import settings
    logger.warning(f"STORAGE BACKEND: {settings.DEFAULT_FILE_STORAGE}")
    logger.warning(f"CLOUDINARY: {getattr(settings, 'CLOUDINARY_STORAGE', 'NOT SET')}")

    try:
        kyc = request.user.kyc_profile
        if kyc.status == 'APPROVED':
            return redirect('kyc:status')
        if kyc.status == 'PENDING':
            messages.info(request, 'Your KYC is currently under review.')
            return redirect('kyc:status')
    except KYCProfile.DoesNotExist:
        kyc = None

    if request.method == 'POST':
        if kyc and kyc.status not in ['NOT_SUBMITTED', 'REJECTED']:
            messages.error(request, 'You cannot resubmit at this stage.')
            return redirect('kyc:status')

        form = KYCSubmitForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.status = 'PENDING'
            profile.save()
            messages.success(request, 'KYC documents submitted successfully! Awaiting review.')
            return redirect('kyc:status')
    else:
        form = KYCSubmitForm(instance=kyc)

    return render(request, 'kyc/submit.html', {'form': form, 'kyc': kyc})


@login_required
def kyc_status_view(request):
    try:
        kyc = request.user.kyc_profile
    except KYCProfile.DoesNotExist:
        kyc = None
    return render(request, 'kyc/status.html', {'kyc': kyc})