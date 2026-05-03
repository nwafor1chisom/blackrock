from django.urls import path
from . import views

app_name = 'kyc'

urlpatterns = [
    path('submit/', views.kyc_submit_view, name='submit'),
    path('status/', views.kyc_status_view, name='status'),
]
