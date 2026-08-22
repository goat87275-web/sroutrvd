"""
Views لتطبيق Orders
Views for orders app - Complete order lifecycle
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from .models import Order, Delivery, Milestone, OrderMessage
from .forms import OrderCreateForm, DeliveryForm, MilestoneForm, OrderMessageForm, CancellationForm
from apps.marketplace.models import Service


class OrderCreateView(LoginRequiredMixin, View):
    """
    إنشاء طلب جديد
    Create new order (Customers only)
    """
    
    def get(self, request, service_id):
        # التحقق من أن المستخدم customer
        if not request.user.is_customer():
            messages.error(request, 'هذه الخدمة متاحة للعملاء فقط.')
            return redirect('marketplace:service_detail', pk=service_id)
        
        service = get_object_or_404(Service, pk=service_id, status='active')
        
        # التحقق من عدم شراء الخدمة من نفسه
        if service.provider == request.user:
            messages.error(request, 'لا يمكنك طلب خدمتك الخاصة!')
            return redirect('marketplace:service_detail', pk=service_id)
        
        form = OrderCreateForm()
        context = {
            'form': form,
            'service': service,
        }
        return render(request, 'orders/order_create.html', context)
    
    def post(self, request, service_id):
        if not request.user.is_customer():
            messages.error(request, 'هذه الخدمة متاحة للعملاء فقط.')
            return redirect('marketplace:service_detail', pk=service_id)
        
        service = get_object_or_404(Service, pk=service_id, status='active')
        form = OrderCreateForm(request.POST)
        
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            order.provider = service.provider
            order.service = service
            order.title = service.title
            order.agreed_price = service.price if service.price else 0
            order.delivery_days = service.delivery_time
            order.save()
            
            messages.success(request, f'تم إنشاء الطلب بنجاح! رقم الطلب: {order.order_number}')
            return redirect('orders:order_detail', order_number=order.order_number)
        
        context = {
            'form': form,
            'service': service,
        }
        return render(request, 'orders/order_create.html', context)


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    تفاصيل الطلب
    Order detail page (Only for order participants)
    """
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()
        # التحقق من أن المستخدم طرف في الطلب
        if request.user != order.customer and request.user != order.provider:
            messages.error(request, 'ليس لديك صلاحية لعرض هذا الطلب.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        
        # النماذج
        context['message_form'] = OrderMessageForm()
        context['delivery_form'] = DeliveryForm()
        context['cancellation_form'] = CancellationForm()
        
        # الرسائل
        context['messages_list'] = order.messages.select_related('sender').all()
        
        # المعالم
        context['milestones'] = order.milestones.all()
        
        # التسليمات
        context['deliveries'] = order.deliveries.all()
        from apps.payments.models import ProviderWallet, Payment
        context['provider_wallets'] = ProviderWallet.objects.filter(provider=order.provider.provider_profile, is_active=True, wallet__is_active=True).select_related('wallet')
        context['latest_payment'] = Payment.objects.filter(order=order).select_related('provider_wallet','provider_wallet__wallet').order_by('-created_at').first()
        
        return context


class OrderListView(LoginRequiredMixin, ListView):
    """
    قائمة طلبات العميل
    Customer's orders list
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_customer():
            messages.error(request, 'هذه الصفحة متاحة للعملاء فقط.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Order.objects.filter(
            customer=self.request.user
        ).select_related('service', 'provider').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = self.get_queryset()
        
        # إحصائيات
        context['active_count'] = orders.filter(status__in=['pending', 'accepted', 'in_progress', 'delivered']).count()
        context['completed_count'] = orders.filter(status='completed').count()
        context['cancelled_count'] = orders.filter(status='cancelled').count()
        
        return context


class ProviderOrdersView(LoginRequiredMixin, ListView):
    """
    قائمة طلبات مقدم الخدمة
    Provider's orders list
    """
    model = Order
    template_name = 'orders/provider_orders.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_provider():
            messages.error(request, 'هذه الصفحة متاحة لمقدمي الخدمات فقط.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Order.objects.filter(
            provider=self.request.user
        ).select_related('service', 'customer').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = self.get_queryset()
        
        # إحصائيات
        context['pending_count'] = orders.filter(status='pending').count()
        context['in_progress_count'] = orders.filter(status='in_progress').count()
        context['completed_count'] = orders.filter(status='completed').count()
        
        return context


@login_required
def order_accept(request, order_number):
    """قبول الطلب (Provider only)"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # التحقق من الصلاحيات
    if request.user != order.provider:
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if not order.can_be_accepted():
        messages.error(request, 'لا يمكن قبول هذا الطلب.')
        return redirect('orders:order_detail', order_number=order_number)
    
    # قبول الطلب
    with transaction.atomic():
        order.transition_to(Order.STATUS_ACCEPTED, actor=request.user)
        order.save()
        order.transition_to(Order.STATUS_PAYMENT_PENDING, actor=request.user)
        order.save()
    
    messages.success(request, 'تم قبول الطلب بنجاح!')
    return redirect('orders:order_detail', order_number=order_number)


@login_required
def order_reject(request, order_number):
    """رفض الطلب (Provider only)"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.user != order.provider:
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if not order.can_be_accepted():
        messages.error(request, 'لا يمكن رفض هذا الطلب.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        form = CancellationForm(request.POST)
        if form.is_valid():
            order.status = Order.STATUS_REJECTED
            order.cancelled_at = timezone.now()
            order.cancellation_reason = form.cleaned_data['reason']
            order.save()
            
            messages.success(request, 'تم رفض الطلب.')
            return redirect('orders:provider_orders')
    
    return redirect('orders:order_detail', order_number=order_number)


@login_required
def order_start(request, order_number):
    """بدء العمل على الطلب (Provider only)"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.user != order.provider:
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if order.payment_status != 'paid':
        messages.error(request, 'لا يمكن بدء العمل قبل تأكيد الدفع.')
        return redirect('orders:order_detail', order_number=order_number)

    if not order.can_be_started():
        messages.error(request, 'لا يمكن بدء العمل على هذا الطلب.')
        return redirect('orders:order_detail', order_number=order_number)
    
    order.transition_to(Order.STATUS_IN_PROGRESS, actor=request.user)
    order.save()
    
    messages.success(request, 'تم بدء العمل على الطلب!')
    return redirect('orders:order_detail', order_number=order_number)


@login_required
def order_deliver(request, order_number):
    """تسليم العمل (Provider only)"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.user != order.provider:
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if not order.can_be_delivered():
        messages.error(request, 'لا يمكن تسليم هذا الطلب.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        form = DeliveryForm(request.POST, request.FILES)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.order = order
            delivery.save()
            
            # تحديث حالة الطلب
            order.transition_to(Order.STATUS_DELIVERED, actor=request.user)
            order.save()
            
            messages.success(request, 'تم تسليم العمل بنجاح! في انتظار مراجعة العميل.')
            return redirect('orders:order_detail', order_number=order_number)
    
    return redirect('orders:order_detail', order_number=order_number)


@login_required
def order_complete(request, order_number):
    """إكمال الطلب (Customer only)"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.user != order.customer:
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if not order.can_be_completed():
        messages.error(request, 'لا يمكن إكمال هذا الطلب.')
        return redirect('orders:order_detail', order_number=order_number)
    
    order.transition_to(Order.STATUS_COMPLETED, actor=request.user)
    order.save()
    
    messages.success(request, 'تم إكمال الطلب بنجاح! شكراً لاستخدامك منصتنا.')
    return redirect('orders:order_detail', order_number=order_number)


@login_required
def order_cancel(request, order_number):
    """إلغاء الطلب (Both parties)"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # التحقق من الصلاحيات
    if request.user not in [order.customer, order.provider]:
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if not order.can_be_cancelled():
        messages.error(request, 'لا يمكن إلغاء هذا الطلب في حالته الحالية.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        form = CancellationForm(request.POST)
        if form.is_valid():
            order.status = Order.STATUS_CANCELLED
            order.cancelled_at = timezone.now()
            order.cancellation_reason = form.cleaned_data['reason']
            order.payment_status = 'refunded' if order.payment_status == 'paid' else 'cancelled'
            order.save()
            
            messages.success(request, 'تم إلغاء الطلب.')
            return redirect('orders:order_detail', order_number=order_number)
    
    return redirect('orders:order_detail', order_number=order_number)


@login_required
def send_order_message(request, order_number):
    """إرسال رسالة حول الطلب"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.user not in [order.customer, order.provider]:
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء.')
        return redirect('home')
    
    if request.method == 'POST':
        form = OrderMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.order = order
            msg.sender = request.user
            msg.save()
            
            messages.success(request, 'تم إرسال الرسالة.')
    
    return redirect('orders:order_detail', order_number=order_number)
