"""
إعدادات لوحة الإدارة لتطبيق accounts
Admin configuration for accounts app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from .models import User, ProviderProfile, ProviderDocumentType, ProviderDocument
from apps.core.services import audit, notify


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'phone', 'city']
    ordering = ['-created_at']
    fieldsets = BaseUserAdmin.fieldsets + (('معلومات إضافية', {'fields': ('role', 'phone', 'city', 'is_verified')}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (('معلومات إضافية', {'fields': ('email', 'role', 'phone', 'city', 'is_verified')}),)


class ProviderDocumentInline(admin.TabularInline):
    model = ProviderDocument
    extra = 0
    fields = ['document_type', 'status', 'reviewed_by', 'reviewed_at', 'review_note', 'view_file_link', 'created_at']
    readonly_fields = ['reviewed_by', 'reviewed_at', 'view_file_link', 'created_at']
    can_delete = False

    def view_file_link(self, obj):
        if not obj or not obj.pk or not obj.file:
            return '-'
        url = reverse('accounts:provider_document_download', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank" rel="noopener">فتح الملف / View File</a>', url)
    view_file_link.short_description = 'فتح الملف'


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_name', 'business_name', 'specialization', 'city', 'district', 'verification_status', 'status', 'is_available', 'created_at']
    list_filter = ['status', 'verification_status', 'is_available', 'city', 'district', 'specialization', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__phone', 'display_name', 'business_name', 'phone', 'email', 'city', 'district', 'specialization', 'bio', 'qualifications', 'experience']
    readonly_fields = ['total_orders', 'completed_orders', 'average_rating', 'created_at', 'updated_at', 'verified_at', 'map_preview']
    ordering = ['-average_rating', '-completed_orders']
    inlines = [ProviderDocumentInline]
    fieldsets = (
        ('المستخدم والحالة', {'fields': ('user', 'status', 'verification_status', 'verified_by', 'verified_at', 'admin_notes')}),
        ('المعلومات الأساسية', {'fields': ('display_name', 'business_name', 'phone', 'email', 'bio', 'profile_image')}),
        ('معلومات النشاط/المهنة', {'fields': ('specialization', 'experience_years', 'hourly_rate', 'qualifications', 'experience', 'is_available', 'availability', 'service_radius')}),
        ('الموقع الجغرافي', {'fields': ('address', 'city', 'district', 'latitude', 'longitude', 'map_preview')}),
        ('الإحصائيات', {'fields': ('total_orders', 'completed_orders', 'average_rating'), 'classes': ('collapse',)}),
        ('التواريخ', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    actions = ['approve_providers', 'reject_providers', 'request_documents', 'suspend_providers']

    def map_preview(self, obj):
        if not obj or obj.latitude is None or obj.longitude is None:
            return 'لا يوجد موقع محفوظ.'
        return format_html(
            '<div style="height:260px;width:100%;max-width:520px;border:1px solid #ddd;border-radius:8px;overflow:hidden">'
            '<iframe width="100%" height="260" style="border:0" loading="lazy" referrerpolicy="no-referrer-when-downgrade" '
            'src="https://www.openstreetmap.org/export/embed.html?bbox={lng1}%2C{lat1}%2C{lng2}%2C{lat2}&layer=mapnik&marker={lat}%2C{lng}"></iframe></div>'
            '<p><strong>Lat:</strong> {lat} &nbsp; <strong>Lng:</strong> {lng}</p>',
            lat=obj.latitude,
            lng=obj.longitude,
            lat1=float(obj.latitude) - 0.01,
            lat2=float(obj.latitude) + 0.01,
            lng1=float(obj.longitude) - 0.01,
            lng2=float(obj.longitude) + 0.01,
        )
    map_preview.short_description = 'معاينة الخريطة'

    def approve_providers(self, request, queryset):
        updated = queryset.update(status='active', verification_status='verified', verified_by=request.user, verified_at=timezone.now())
        self.message_user(request, f'تم الموافقة على {updated} مقدم خدمة.')
    approve_providers.short_description = 'الموافقة على مقدمي الخدمات المحددين'

    def reject_providers(self, request, queryset):
        updated = queryset.update(status='inactive', verification_status='rejected')
        self.message_user(request, f'تم رفض {updated} مقدم خدمة.')
    reject_providers.short_description = 'رفض مقدمي الخدمات المحددين'

    def request_documents(self, request, queryset):
        updated = queryset.update(status='inactive', verification_status='needs_documents')
        self.message_user(request, f'تم طلب مستندات إضافية من {updated} مقدم خدمة.')
    request_documents.short_description = 'طلب مستندات إضافية'

    def suspend_providers(self, request, queryset):
        updated = queryset.update(status='suspended', verification_status='suspended')
        self.message_user(request, f'تم إيقاف {updated} مقدم خدمة.')
    suspend_providers.short_description = 'إيقاف مقدمي الخدمات'


@admin.register(ProviderDocumentType)
class ProviderDocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_required', 'is_active', 'created_at']
    list_filter = ['is_required', 'is_active']
    search_fields = ['code', 'name']


@admin.register(ProviderDocument)
class ProviderDocumentAdmin(admin.ModelAdmin):
    list_display = ['provider', 'document_type', 'status', 'reviewed_by', 'reviewed_at', 'created_at', 'view_file_link']
    list_filter = ['status', 'document_type', 'created_at']
    search_fields = ['provider__user__username', 'provider__user__email', 'document_type__name', 'document_type__code']
    raw_id_fields = ['provider', 'reviewed_by']
    readonly_fields = ['view_file_link', 'created_at', 'updated_at', 'reviewed_at']
    fields = ['provider', 'document_type', 'file', 'view_file_link', 'status', 'reviewed_by', 'reviewed_at', 'review_note', 'created_at', 'updated_at']
    actions = ['approve_documents', 'reject_documents', 'request_more_documents']

    def view_file_link(self, obj):
        if not obj or not obj.pk or not obj.file:
            return '-'
        url = reverse('accounts:provider_document_download', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank" rel="noopener">فتح الملف / View File</a>', url)
    view_file_link.short_description = 'فتح الملف'

    def _review(self, request, queryset, status, event):
        for doc in queryset:
            doc.status = status
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
            notify(doc.provider.user, event, 'تحديث مستندات التوثيق', f'تم تحديث حالة المستند: {doc.document_type.name}')
            audit(request.user, f'document_{status}', doc)

    def approve_documents(self, request, queryset):
        self._review(request, queryset, 'approved', 'provider_verified')
    approve_documents.short_description = 'اعتماد المستندات المحددة'

    def reject_documents(self, request, queryset):
        self._review(request, queryset, 'rejected', 'provider_rejected')
    reject_documents.short_description = 'رفض المستندات المحددة'

    def request_more_documents(self, request, queryset):
        self._review(request, queryset, 'needs_additional_documents', 'documents_requested')
    request_more_documents.short_description = 'طلب مستندات إضافية'
