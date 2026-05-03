from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_methods_view, name='methods'),
    path('<uuid:pk>/', views.payment_method_detail, name='method_detail'),
]
