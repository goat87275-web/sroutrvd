from django.db import models
from django.core.validators import MinValueValidator, RegexValidator

wallet_account_validator = RegexValidator(regex=r'^\+?[0-9]{6,20}$', message='رقم الحساب يجب أن يحتوي على 6 إلى 20 رقمًا ويمكن أن يبدأ بـ +.')

class Wallet(models.Model):
    name=models.CharField(max_length=80)
    code=models.SlugField(max_length=50, unique=True)
    color=models.CharField(max_length=20, default='#0d6efd')
    is_active=models.BooleanField(default=True, db_index=True)
    display_order=models.PositiveIntegerField(default=0, db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=['display_order','name']
    def __str__(self): return self.name

class ProviderWallet(models.Model):
    provider=models.ForeignKey('accounts.ProviderProfile',on_delete=models.CASCADE,related_name='wallet_accounts')
    wallet=models.ForeignKey(Wallet,on_delete=models.PROTECT,related_name='provider_accounts')
    account_number=models.CharField(max_length=30, validators=[wallet_account_validator])
    is_active=models.BooleanField(default=True, db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=[('provider','wallet')]
        indexes=[models.Index(fields=['provider','is_active']), models.Index(fields=['wallet','is_active'])]
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.wallet_id and not self.wallet.is_active:
            raise ValidationError('لا يمكن استخدام محفظة غير نشطة.')
        if self.is_active and not self.account_number:
            raise ValidationError('رقم الحساب مطلوب عند تفعيل المحفظة.')
    def __str__(self): return f'{self.provider} - {self.wallet}'

class Payment(models.Model):
    STATUS_PENDING='pending'; STATUS_PROCESSING='processing'; STATUS_UNDER_REVIEW='under_review'; STATUS_PAID='paid'; STATUS_FAILED='failed'; STATUS_REJECTED='rejected'; STATUS_REFUNDED='refunded'; STATUS_CANCELLED='cancelled'
    STATUS_CHOICES=[(STATUS_PENDING,'في الانتظار'),(STATUS_PROCESSING,'قيد المعالجة'),(STATUS_UNDER_REVIEW,'قيد مراجعة السند'),(STATUS_PAID,'مدفوع'),(STATUS_FAILED,'فشل'),(STATUS_REJECTED,'مرفوض'),(STATUS_REFUNDED,'مسترد'),(STATUS_CANCELLED,'ملغي')]
    order=models.ForeignKey('orders.Order',on_delete=models.CASCADE,related_name='payments')
    provider_wallet=models.ForeignKey(ProviderWallet,on_delete=models.PROTECT,null=True,blank=True,related_name='payments')
    provider_wallet_account_snapshot=models.CharField(max_length=30, blank=True)
    amount=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0)])
    currency=models.CharField(max_length=3,default='YER')
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default=STATUS_PENDING,db_index=True)
    payment_method=models.CharField(max_length=50,default='manual_wallet')
    transaction_id=models.CharField(max_length=120,blank=True,db_index=True)
    gateway=models.CharField(max_length=80,default='manual_wallet')
    proof_file=models.FileField(upload_to='payment_proofs/%Y/%m/', blank=True, null=True)
    proof_uploaded_at=models.DateTimeField(null=True,blank=True)
    reviewed_by=models.ForeignKey('accounts.User',on_delete=models.SET_NULL,null=True,blank=True,related_name='reviewed_payments')
    reviewed_at=models.DateTimeField(null=True,blank=True)
    review_note=models.TextField(blank=True)
    commission_rate=models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    commission_amount=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    provider_net_amount=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    paid_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        indexes=[models.Index(fields=['status','created_at']),models.Index(fields=['payment_method','created_at'])]
        permissions=[('manage_payments','Can manage payments')]
    def __str__(self): return f'{self.order} - {self.amount} {self.currency}'

class CommissionRecord(models.Model):
    order=models.OneToOneField('orders.Order',on_delete=models.CASCADE,related_name='commission_record')
    payment=models.OneToOneField(Payment,on_delete=models.SET_NULL,null=True,blank=True,related_name='commission_record')
    commission_rate=models.DecimalField(max_digits=5,decimal_places=2)
    gross_amount=models.DecimalField(max_digits=10,decimal_places=2)
    commission_amount=models.DecimalField(max_digits=10,decimal_places=2)
    provider_net_amount=models.DecimalField(max_digits=10,decimal_places=2)
    currency=models.CharField(max_length=3,default='YER')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: permissions=[('manage_commissions','Can manage commissions')]
