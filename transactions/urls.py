from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('deposit/', views.deposit_view, name='deposit'),
    path('deposit/<uuid:pk>/confirm/', views.deposit_confirm_view, name='deposit_confirm'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('history/', views.history_view, name='history'),
]
