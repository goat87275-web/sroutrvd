from django.contrib import admin
from .models import TermsAndConditions, TermsAcceptance, PlatformSetting, Notification, AuditLog, City, District
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display=['name','is_active','order','created_at']; list_filter=['is_active']; search_fields=['name']; ordering=['order','name']
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display=['name','city','is_active','order','created_at']; list_filter=['is_active','city']; search_fields=['name','city__name']; list_select_related=['city']; ordering=['city','order','name']
@admin.register(TermsAndConditions)
class TermsAdmin(admin.ModelAdmin): list_display=['version','commission_rate','is_active','published_at','created_at']; list_filter=['is_active']; search_fields=['version','content']
@admin.register(TermsAcceptance)
class TermsAcceptanceAdmin(admin.ModelAdmin): list_display=['user','terms','commission_rate','accepted_at','ip_address']; list_filter=['accepted_at']; search_fields=['user__username','terms__version']
@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin): list_display=['key','value','updated_at']; search_fields=['key','value']
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin): list_display=['recipient','event_type','title','is_read','created_at']; list_filter=['event_type','is_read','created_at']; search_fields=['recipient__username','title','message']
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin): list_display=['actor','action','content_type','object_id','created_at']; list_filter=['action','created_at']; readonly_fields=['actor','action','content_type','object_id','metadata','created_at']
