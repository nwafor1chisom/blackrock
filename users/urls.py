from django.urls import path
from . import views
from . import reset_views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Password reset flow (3-step OTP system)
    path('forgot-password/', reset_views.forgot_password_view, name='forgot_password'),
    path('verify-otp/<uuid:token>/', reset_views.verify_otp_view, name='verify_otp'),
    path('reset-password/<uuid:token>/', reset_views.reset_password_view, name='reset_password'),
]
