from django.urls import path
from . import views

app_name = 'referral'

urlpatterns = [
    path('', views.referral_dashboard_view, name='dashboard'),
]
