from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PaymentMethod


@login_required
def payment_methods_view(request):
    methods = PaymentMethod.objects.filter(is_active=True)
    return render(request, 'payments/methods.html', {'methods': methods})


@login_required
def payment_method_detail(request, pk):
    method = get_object_or_404(PaymentMethod, pk=pk, is_active=True)
    return render(request, 'payments/method_detail.html', {'method': method})
