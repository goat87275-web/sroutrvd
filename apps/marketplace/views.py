"""
Views لتطبيق Marketplace
Views for marketplace app - Services and Categories
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from .models import Category, Service, ProviderService
from .forms import ServiceForm, ServiceSearchForm
from apps.accounts.models import User
from apps.core.models import City, District
from apps.accounts.utils import is_provider_verified
from apps.orders.models import Order


def home_view(request):
    """الصفحة الرئيسية"""
    # إحصائيات
    stats = {
        'services_count': Service.objects.filter(status='active', provider__provider_profile__status='active', provider__provider_profile__verification_status='verified').count(),
        'providers_count': User.objects.filter(role='provider', provider_profile__status='active', provider_profile__verification_status='verified').count(),
        'orders_count': Order.objects.filter(status='completed').count(),
    }
    
    # أحدث الخدمات (آخر 6)
    latest_services = Service.objects.filter(
        status='active',
        provider__provider_profile__status='active', provider__provider_profile__verification_status='verified'
    ).select_related('provider', 'category').order_by('-created_at')[:6]
    
    # الخدمات الأعلى تقييماً (6 خدمات)
    top_rated_services = Service.objects.filter(
        status='active',
        provider__provider_profile__status='active', provider__provider_profile__verification_status='verified',
        average_rating__gte=4.0
    ).select_related('provider', 'category').order_by('-average_rating', '-created_at')[:6]
    
    # التصنيفات الرئيسية (أول 6)
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).prefetch_related('services')[:6]
    
    context = {
        'stats': stats,
        'latest_services': latest_services,
        'top_rated_services': top_rated_services,
        'categories': categories,
    }
    
    return render(request, 'home.html', context)


class ServiceListView(ListView):
    """
    قائمة الخدمات مع البحث والفلترة
    Service list with search and filters
    """
    model = Service
    template_name = 'marketplace/service_list.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Service.objects.filter(
            status='active',
            provider__provider_profile__status='active', provider__provider_profile__verification_status='verified'
        ).select_related(
            'provider', 'provider__provider_profile', 'category'
        )
        
        # 1. البحث النصي
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(provider__username__icontains=q)
            )
        
        # 2. الفلترة حسب التصنيف
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # 3. الفلترة حسب السعر (من وإلى)
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # 4. الترتيب (مرن لاستقبال التسميات المختلفة sort_by أو ordering أو sort)
        sort_by = self.request.GET.get('ordering') or self.request.GET.get('sort_by') or self.request.GET.get('sort')
        
        if sort_by in ['price_asc', 'price']:
            queryset = queryset.order_by('price')
        elif sort_by in ['price_desc', '-price']:
            queryset = queryset.order_by('-price')
        elif sort_by in ['rating', '-average_rating']:
            queryset = queryset.order_by('-average_rating')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 🎯 تم إزالة self.request.GET لمنع تعبئة الخانات بعد البحث تلقائياً
        context['search_form'] = ServiceSearchForm()
        context['categories'] = Category.objects.filter(is_active=True)
        context['total_count'] = self.get_queryset().count()
        return context


class ServiceDetailView(DetailView):
    """
    تفاصيل الخدمة
    Service detail page
    """
    model = Service
    template_name = 'marketplace/service_detail.html'
    context_object_name = 'service'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_object()
        
        # زيادة عداد المشاهدات
        service.increment_views()
        
        # خدمات مشابهة من نفس التصنيف
        if service.category:
            context['related_services'] = Service.objects.filter(
                category=service.category,
                status='active',
                provider__provider_profile__status='active', provider__provider_profile__verification_status='verified'
            ).exclude(id=service.id).select_related('provider')[:4]
        
        return context


class ServiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    إضافة خدمة جديدة
    Create new service (Providers only)
    """
    model = Service
    form_class = ServiceForm
    template_name = 'marketplace/service_form.html'
    success_url = reverse_lazy('marketplace:my_services')
    
    def test_func(self):
        """فقط المقدمين يمكنهم إضافة خدمات"""
        return self.request.user.is_provider() and is_provider_verified(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, 'يجب تفعيل/توثيق حساب مقدم الخدمة قبل إضافة الخدمات.')
        return redirect('accounts:provider_profile_edit')
    
    def form_valid(self, form):
        form.instance.provider = self.request.user
        messages.success(self.request, 'تم إضافة الخدمة بنجاح.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'إضافة خدمة جديدة'
        context['button_text'] = 'نشر الخدمة'
        return context


class ServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    تعديل خدمة
    Update service (Owner only)
    """
    model = Service
    form_class = ServiceForm
    template_name = 'marketplace/service_form.html'
    
    def test_func(self):
        """فقط المالك يمكنه التعديل"""
        service = self.get_object()
        return service.is_owned_by(self.request.user)
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الخدمة بنجاح!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'تعديل الخدمة'
        context['button_text'] = 'حفظ التغييرات'
        return context


class ServiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    حذف خدمة
    Delete service (Owner only)
    """
    model = Service
    template_name = 'marketplace/service_confirm_delete.html'
    success_url = reverse_lazy('marketplace:my_services')
    
    def test_func(self):
        """فقط المالك يمكنه الحذف"""
        service = self.get_object()
        return service.is_owned_by(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف الخدمة بنجاح.')
        return super().delete(request, *args, **kwargs)


@login_required
def my_services_view(request):
    """
    صفحة خدمات المقدم
    Provider's services page
    """
    if not request.user.is_provider():
        messages.error(request, 'هذه الصفحة متاحة لمقدمي الخدمات فقط.')
        return redirect('home')
    
    services = Service.objects.filter(provider=request.user).select_related('category')
    
    # إحصائيات
    active_count = services.filter(status='active').count()
    paused_count = services.filter(status='paused').count()
    total_views = sum(s.views_count for s in services)
    total_orders = sum(s.orders_count for s in services)
    
    context = {
        'services': services,
        'active_count': active_count,
        'paused_count': paused_count,
        'total_views': total_views,
        'total_orders': total_orders,
    }
    
    return render(request, 'marketplace/my_services.html', context)


class CategoryListView(ListView):
    """
    قائمة التصنيفات
    Categories list
    """
    model = Category
    template_name = 'marketplace/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # فقط التصنيفات الرئيسية النشطة
        return Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).prefetch_related('subcategories')


class CategoryDetailView(DetailView):
    """
    تفاصيل التصنيف (الخدمات المرتبطة به)
    Category detail with related services
    """
    model = Category
    template_name = 'marketplace/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        # الخدمات في هذا التصنيف
        services = Service.objects.filter(
            category=category,
            status='active',
            provider__provider_profile__status='active', provider__provider_profile__verification_status='verified'
        ).select_related('provider', 'provider__provider_profile')
        
        context['services'] = services
        context['services_count'] = services.count()
        
        return context

class ProviderSearchView(ListView):
    template_name = 'marketplace/provider_search.html'
    context_object_name = 'providers'
    paginate_by = 12
    def get_queryset(self):
        from .search import filter_public_providers
        return filter_public_providers(self.request.GET)
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context['categories']=Category.objects.filter(is_active=True)
        context['services']=Service.objects.filter(status='active')
        context['cities']=City.objects.filter(is_active=True)
        context['districts']=District.objects.filter(is_active=True)
        context['params']=self.request.GET
        return context

class GlobalSearchView(TemplateView):
    template_name='marketplace/global_search.html'
    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        from .search import filter_public_services, filter_public_categories, filter_public_providers
        context=super().get_context_data(**kwargs)
        q=self.request.GET.get('q','').strip()
        context['q']=q
        context['services']=filter_public_services(self.request.GET)[:10]
        context['categories']=filter_public_categories(self.request.GET)[:10]
        context['providers']=filter_public_providers(self.request.GET)
        if not isinstance(context['providers'], list): context['providers']=context['providers'][:10]
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            from apps.orders.models import Order
            from apps.payments.models import Payment
            from apps.reviews.models import Review
            from apps.core.models import Notification
            from apps.accounts.models import ProviderDocument
            if q:
                context['admin_users']=User.objects.filter(Q(username__icontains=q)|Q(email__icontains=q)|Q(phone__icontains=q))[:10]
                context['admin_orders']=Order.objects.filter(Q(order_number__icontains=q)|Q(customer__username__icontains=q)|Q(provider__username__icontains=q)|Q(service__title__icontains=q)).select_related('customer','provider','service')[:10]
                context['admin_payments']=Payment.objects.filter(Q(transaction_id__icontains=q)|Q(order__order_number__icontains=q)|Q(order__customer__username__icontains=q)|Q(order__provider__username__icontains=q)).select_related('order')[:10]
                context['admin_reviews']=Review.objects.filter(Q(customer__username__icontains=q)|Q(provider__username__icontains=q)|Q(service__title__icontains=q)|Q(order__order_number__icontains=q)).select_related('customer','provider','service','order')[:10]
                context['admin_documents']=ProviderDocument.objects.filter(Q(provider__user__username__icontains=q)|Q(document_type__name__icontains=q)).select_related('provider__user','document_type')[:10]
                context['admin_notifications']=Notification.objects.filter(Q(title__icontains=q)|Q(message__icontains=q)|Q(recipient__username__icontains=q))[:10]
        return context
