from django.contrib import admin
from .models import Wallet, ProviderWallet, Payment, CommissionRecord

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display=['display_order','name','code','color','is_active','updated_at']
    list_filter=['is_active']
    search_fields=['name','code']
    ordering=['display_order','name']

@admin.register(ProviderWallet)
class ProviderWalletAdmin(admin.ModelAdmin):
    list_display=['provider','wallet','account_number','is_active','updated_at']
    list_filter=['is_active','wallet']
    search_fields=['provider__user__username','wallet__name','account_number']
    raw_id_fields=['provider']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display=['order','amount','currency','status','provider_wallet','commission_rate','commission_amount','provider_net_amount','reviewed_by','reviewed_at','created_at']
    list_filter=['status','payment_method','gateway','created_at','provider_wallet__wallet']
    search_fields=['order__order_number','transaction_id','provider_wallet_account_snapshot']
    raw_id_fields=['order','provider_wallet','reviewed_by']
    readonly_fields=['created_at','updated_at','paid_at','proof_uploaded_at']

@admin.register(CommissionRecord)
class CommissionAdmin(admin.ModelAdmin):
    list_display=['order','gross_amount','commission_rate','commission_amount','provider_net_amount','currency','created_at']
    list_filter=['currency','created_at']
    search_fields=['order__order_number']
