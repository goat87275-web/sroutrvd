from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.http import require_POST
from apps.orders.models import Order
from .forms import PaymentProofForm, PaymentRejectForm
from .models import Payment, ProviderWallet
from .services import create_payment, mark_payment_paid, mark_payment_failed, submit_payment_proof

@login_required
def payment_create(request, order_number):
    order=get_object_or_404(Order.objects.select_related('service','provider','provider__provider_profile'), order_number=order_number, customer=request.user)
    if order.status != Order.STATUS_PAYMENT_PENDING:
        messages.error(request,'لا يمكن إنشاء دفع لهذا الطلب حالياً.')
        return redirect('orders:order_detail', order_number=order_number)
    if request.method != 'POST':
        messages.error(request, 'يجب اختيار محفظة للدفع.')
        return redirect('orders:order_detail', order_number=order_number)
    wallet=get_object_or_404(ProviderWallet.objects.select_related('wallet','provider'), pk=request.POST.get('provider_wallet'), provider=order.provider.provider_profile, is_active=True, wallet__is_active=True)
    try:
        payment=create_payment(order, provider_wallet=wallet, method='manual_wallet')
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('orders:order_detail', order_number=order_number)
    return redirect('payments:payment_detail', pk=payment.pk)

@login_required
def payment_detail(request, pk):
    payment=get_object_or_404(Payment.objects.select_related('order','order__service','order__provider','order__customer','provider_wallet','provider_wallet__wallet'), pk=pk)
    if request.user not in [payment.order.customer, payment.order.provider] and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية لعرض هذه الدفعة.')
        return redirect('home')
    return render(request,'payments/payment_detail.html',{'payment':payment,'proof_form':PaymentProofForm(instance=payment),'reject_form':PaymentRejectForm(),'debug_payment_actions':settings.DEBUG})

@login_required
@require_POST
def payment_submit_proof(request, pk):
    payment=get_object_or_404(Payment, pk=pk, order__customer=request.user)
    form=PaymentProofForm(request.POST, request.FILES, instance=payment)
    if form.is_valid():
        submit_payment_proof(payment, form.cleaned_data['proof_file'], actor=request.user)
        messages.success(request, 'تم رفع سند الحوالة وإرساله لمقدم الخدمة للمراجعة.')
    else:
        messages.error(request, 'تعذر رفع سند الحوالة. تحقق من نوع وحجم الملف.')
    return redirect('payments:payment_detail', pk=pk)

@login_required
@require_POST
def payment_approve(request, pk):
    payment=get_object_or_404(Payment, pk=pk, order__provider=request.user)
    if payment.status != Payment.STATUS_UNDER_REVIEW:
        messages.error(request, 'لا يمكن اعتماد دفعة ليست قيد المراجعة.')
    else:
        mark_payment_paid(payment, actor=request.user)
        messages.success(request, 'تم تأكيد الدفع وتحديث الطلب.')
    return redirect('orders:order_detail', order_number=payment.order.order_number)

@login_required
@require_POST
def payment_reject(request, pk):
    payment=get_object_or_404(Payment, pk=pk, order__provider=request.user)
    form=PaymentRejectForm(request.POST)
    if payment.status != Payment.STATUS_UNDER_REVIEW:
        messages.error(request, 'لا يمكن رفض دفعة ليست قيد المراجعة.')
    elif form.is_valid():
        mark_payment_failed(payment, actor=request.user, reason=form.cleaned_data['reason'])
        messages.success(request, 'تم رفض سند الحوالة وإشعار العميل.')
    else:
        messages.error(request, 'سبب الرفض مطلوب.')
    return redirect('payments:payment_detail', pk=pk)

@login_required
@require_POST
def payment_test_success(request, pk):
    if not settings.DEBUG:
        messages.error(request, 'تأكيد الدفع التجريبي غير متاح في الإنتاج.')
        return redirect('payments:payment_detail', pk=pk)
    payment=get_object_or_404(Payment, pk=pk, order__customer=request.user)
    mark_payment_paid(payment, actor=request.user)
    messages.success(request, 'تم تأكيد الدفع التجريبي وتحديث الطلب.')
    return redirect('orders:order_detail', order_number=payment.order.order_number)

@login_required
@require_POST
def payment_test_fail(request, pk):
    if not settings.DEBUG:
        messages.error(request, 'فشل الدفع التجريبي غير متاح في الإنتاج.')
        return redirect('payments:payment_detail', pk=pk)
    payment=get_object_or_404(Payment, pk=pk, order__customer=request.user)
    mark_payment_failed(payment, actor=request.user, reason='debug-test-failure')
    messages.error(request, 'تم تسجيل فشل الدفع التجريبي ولم يتم جعل الطلب مدفوعاً.')
    return redirect('payments:payment_detail', pk=pk)
