"""
إعدادات لوحة الإدارة لتطبيق Marketplace
Admin configuration for marketplace app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Service, ProviderService, ManagedService, Specialization, Qualification

class CatalogChoiceAdmin(admin.ModelAdmin):
    list_display=['name','is_active','order','updated_at']; list_filter=['is_active']; search_fields=['name']; ordering=['order','name']
@admin.register(Specialization)
class SpecializationAdmin(CatalogChoiceAdmin): pass
@admin.register(Qualification)
class QualificationAdmin(CatalogChoiceAdmin): pass
@admin.register(ManagedService)
class ManagedServiceAdmin(CatalogChoiceAdmin):
    list_display=['name','category','is_active','order','updated_at']; list_filter=['is_active','category']; search_fields=['name','description','category__name']
    fieldsets=(('الخدمة',{'fields':('name','description','category')}),('النشر',{'fields':('is_active','order')}))


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    إدارة التصنيفات
    Category admin
    """
    list_display = ['name', 'parent', 'is_active', 'order', 'get_services_count', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'description', 'icon')
        }),
        ('التنظيم', {
            'fields': ('parent', 'order', 'is_active')
        }),
    )
    
    def get_services_count(self, obj):
        """عرض عدد الخدمات"""
        return obj.get_services_count()
    get_services_count.short_description = 'عدد الخدمات'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    إدارة الخدمات
    Service admin
    """
    list_display = [
        'title', 'provider', 'category', 'price_type', 
        'price', 'get_status_badge', 'views_count', 'orders_count',
        'average_rating', 'is_featured', 'created_at'
    ]
    list_filter = ['status', 'price_type', 'is_featured', 'category', 'created_at']
    search_fields = ['title', 'description', 'provider__username']
    readonly_fields = ['views_count', 'orders_count', 'average_rating', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('provider', 'category', 'title', 'description', 'image')
        }),
        ('التسعير والتسليم', {
            'fields': ('price_type', 'price', 'delivery_time')
        }),
        ('الحالة والمميزات', {
            'fields': ('status', 'is_featured')
        }),
        ('الإحصائيات', {
            'fields': ('views_count', 'orders_count', 'average_rating'),
            'classes': ('collapse',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_active', 'make_paused', 'make_featured']
    
    def get_status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'active': 'success',
            'paused': 'secondary',
            'closed': 'danger',
        }
        labels = dict(Service.STATUS_CHOICES)
        return format_html('<span class="badge bg-{}">{}</span>', colors.get(obj.status, 'secondary'), labels.get(obj.status, obj.status))
    get_status_badge.short_description = 'الحالة المستحدثة'
    
    def make_active(self, request, queryset):
        """تفعيل الخدمات المحددة"""
        updated = queryset.update(status='active')
        self.message_user(request, f'تم تفعيل {updated} خدمة.')
    make_active.short_description = 'تفعيل الخدمات المحددة'
    
    def make_paused(self, request, queryset):
        """إيقاف الخدمات المحددة"""
        updated = queryset.update(status='paused')
        self.message_user(request, f'تم إيقاف {updated} خدمة.')
    make_paused.short_description = 'إيقاف الخدمات المحددة'
    
    def make_featured(self, request, queryset):
        """جعل الخدمات مميزة"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'تم جعل {updated} خدمة مميزة.')
    make_featured.short_description = 'جعل الخدمات مميزة'

@admin.register(ProviderService)
class ProviderServiceAdmin(admin.ModelAdmin):
    list_display=['provider','catalog_service','service','approval_status','price','price_type','estimated_duration','is_active','created_at']
    list_filter=['approval_status','is_active','price_type','catalog_service','service__category','created_at']
    search_fields=['provider__user__username','service__title','catalog_service__name','description']
    raw_id_fields=['provider','service']
