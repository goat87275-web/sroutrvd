"""
موديلات المستخدمين والملفات الشخصية
User and Profile models for the accounts app
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from .storage import PrivateMediaStorage


class User(AbstractUser):
    """
    موديل المستخدم المخصص مع أدوار مختلفة
    Custom User model with role system
    """
    ROLE_CHOICES = (
        ('customer', 'عميل'),
        ('provider', 'مقدم خدمة'),
        ('admin', 'مدير'),
        ('super_admin', 'مدير عام'),
    )
    
    # الحقول الأساسية
    email = models.EmailField('البريد الإلكتروني', unique=True)
    role = models.CharField('الدور', max_length=20, choices=ROLE_CHOICES, default='customer')
    
    
    # معلومات إضافية
    phone = models.CharField('رقم الجوال', max_length=20, blank=True)
    city = models.CharField('المدينة', max_length=100, blank=True)
    
    # حالة الحساب
    is_verified = models.BooleanField('حساب موثق', default=False)
    is_active = models.BooleanField('حساب نشط', default=True)
    
    # تواريخ
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    # استخدام email كاسم مستخدم
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_customer(self):
        """تحقق إذا كان المستخدم عميل"""
        return self.role == 'customer'
    
    def is_provider(self):
        """تحقق إذا كان المستخدم مقدم خدمة"""
        return self.role == 'provider'
    
    def is_admin_role(self):
        """تحقق إذا كان المستخدم مدير"""
        return self.role in ['admin', 'super_admin'] or self.is_superuser


class ProviderProfile(models.Model):
    """
    الملف الشخصي لمقدم الخدمة
    Provider profile with additional information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    
    # معلومات شخصية
    business_name = models.CharField('اسم العمل', max_length=150, blank=True)
    display_name = models.CharField('اسم العرض', max_length=150, blank=True)
    phone = models.CharField('هاتف العمل', max_length=20, blank=True)
    email = models.EmailField('بريد العمل', blank=True)
    qualifications = models.TextField('المؤهلات', blank=True)
    experience = models.TextField('الخبرات', blank=True)
    bio = models.TextField('نبذة تعريفية', max_length=500, blank=True)
    profile_image = models.ImageField('صورة الملف الشخصي', upload_to='profiles/', blank=True, null=True)
    
    # معلومات العمل
    specialization = models.CharField('التخصص', max_length=100, blank=True, 
                                     help_text='مثال: تصميم جرافيك، برمجة ويب، تسويق')
    experience_years = models.PositiveIntegerField('سنوات الخبرة', default=0, db_index=True)
    hourly_rate = models.DecimalField('السعر بالساعة', max_digits=10, decimal_places=2, 
                                      null=True, blank=True, help_text='بالريال اليمني')
    
    # موقع جغرافي
    address = models.TextField('العنوان', blank=True)
    city = models.CharField('المدينة', max_length=100, blank=True, db_index=True)
    district = models.CharField('المنطقة', max_length=100, blank=True, db_index=True)
    latitude = models.DecimalField('خط العرض', max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField('خط الطول', max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    service_radius = models.PositiveIntegerField('نطاق الخدمة بالكيلومتر', default=10)
    availability = models.CharField('التوفر', max_length=120, blank=True)
    
    # إحصائيات
    total_orders = models.PositiveIntegerField('إجمالي الطلبات', default=0)
    completed_orders = models.PositiveIntegerField('الطلبات المكتملة', default=0)
    average_rating = models.DecimalField('متوسط التقييم', max_digits=3, decimal_places=2, 
                                         default=0.00, help_text='من 0 إلى 5')
    
    # حالة
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('suspended', 'موقوف'),
    ]
    status = models.CharField('حالة الحساب', max_length=20, choices=STATUS_CHOICES, default='inactive', db_index=True)
    VERIFICATION_STATUS_CHOICES = [('unverified','غير موثق'),('pending_review','قيد المراجعة'),('verified','موثق'),('rejected','مرفوض'),('needs_documents','يحتاج مستندات'),('suspended','موقوف')]
    verification_status = models.CharField('حالة التوثيق', max_length=30, choices=VERIFICATION_STATUS_CHOICES, default='unverified', db_index=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_provider_profiles')
    verified_at = models.DateTimeField('وقت التوثيق', null=True, blank=True)
    admin_notes = models.TextField('ملاحظات الإدارة', blank=True)
    is_available = models.BooleanField('متاح لطلبات جديدة', default=True)
    
    # تواريخ
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    class Meta:
        verbose_name = 'ملف مقدم خدمة'
        verbose_name_plural = 'ملفات مقدمي الخدمات'
        ordering = ['-average_rating', '-completed_orders']
        indexes = [models.Index(fields=['verification_status','city']), models.Index(fields=['status','is_available'])]
    
    def __str__(self):
        return f"ملف {self.user.username}"
    
    def get_completion_rate(self):
        """حساب نسبة إتمام الطلبات"""
        if self.total_orders == 0:
            return 0
        return round((self.completed_orders / self.total_orders) * 100, 2)
    
    def update_stats(self):
        """تحديث الإحصائيات من الطلبات"""
        from apps.orders.models import Order
        orders = Order.objects.filter(provider=self.user)
        self.total_orders = orders.count()
        self.completed_orders = orders.filter(status=Order.STATUS_COMPLETED).count()
        self.save()

class ProviderDocumentType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'نوع مستند مقدم الخدمة'; verbose_name_plural = 'أنواع مستندات مقدمي الخدمات'
    def __str__(self): return self.name

def provider_document_path(instance, filename):
    from django.utils.text import get_valid_filename
    return f"provider_documents/provider_{instance.provider_id}/{get_valid_filename(filename)}"

class ProviderDocument(models.Model):
    STATUS_CHOICES=[('pending','قيد المراجعة'),('approved','مقبول'),('rejected','مرفوض'),('needs_additional_documents','يحتاج مستندات إضافية')]
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(ProviderDocumentType, on_delete=models.PROTECT, related_name='documents')
    file = models.FileField(upload_to=provider_document_path, storage=PrivateMediaStorage())
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='pending', db_index=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_provider_documents')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name='مستند مقدم خدمة'; verbose_name_plural='مستندات مقدمي الخدمات'
        permissions=[('review_provider_document','Can review provider document'),('verify_provider','Can verify provider')]
        indexes=[models.Index(fields=['provider','status']), models.Index(fields=['document_type','status'])]
    def can_be_viewed_by(self, user):
        return user.is_authenticated and (user == self.provider.user or user.is_staff or user.has_perm('accounts.review_provider_document') or user.is_superuser)
    def __str__(self): return f'{self.provider} - {self.document_type}'
