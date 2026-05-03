from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('deposits/', views.admin_deposits, name='deposits'),
    path('deposits/<uuid:pk>/action/', views.admin_deposit_action, name='deposit_action'),
    path('withdrawals/', views.admin_withdrawals, name='withdrawals'),
    path('withdrawals/<uuid:pk>/action/', views.admin_withdrawal_action, name='withdrawal_action'),
    path('kyc/', views.admin_kyc, name='kyc'),
    path('kyc/<uuid:pk>/action/', views.admin_kyc_action, name='kyc_action'),
    path('bonus/', views.admin_credit_bonus, name='credit_bonus'),
    path('referrals/', views.admin_referrals, name='referrals'),
    path('referrals/<uuid:pk>/action/', views.admin_referral_action, name='referral_action'),
    path('users/', views.admin_users, name='users'),
    path('users/<uuid:pk>/', views.admin_user_detail, name='user_detail'),
]
