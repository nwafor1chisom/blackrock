from django.urls import path
from . import views

app_name = 'ledger'

urlpatterns = [
    path('history/', views.history_view, name='history'),
]
