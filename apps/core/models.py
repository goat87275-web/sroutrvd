from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class City(models.Model):
    """A centrally managed, selectable city; never hard-code locations in forms."""
    name = models.CharField('اسم المدينة', max_length=100, unique=True)
    is_active = models.BooleanField('نشطة', default=True, db_index=True)
    order = models.PositiveIntegerField('الترتيب', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مدينة'; verbose_name_plural = 'المدن'
        ordering = ['order', 'name']

    def __str__(self): return self.name


class District(models.Model):
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='districts', verbose_name='المدينة')
    name = models.CharField('اسم المديرية', max_length=100)
    is_active = models.BooleanField('نشطة', default=True, db_index=True)
    order = models.PositiveIntegerField('الترتيب', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مديرية'; verbose_name_plural = 'المديريات'
        ordering = ['city__order', 'order', 'name']
        constraints = [models.UniqueConstraint(fields=['city', 'name'], name='unique_district_per_city')]
        indexes = [models.Index(fields=['city', 'is_active'])]

    def __str__(self): return f'{self.city} - {self.name}'

class TermsAndConditions(models.Model):
    version=models.CharField(max_length=30, unique=True)
    content=models.TextField()
    commission_rate=models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active=models.BooleanField(default=False, db_index=True)
    published_at=models.DateTimeField(null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name='شروط وأحكام'; verbose_name_plural='الشروط والأحكام'
        permissions=[('manage_terms','Can manage terms')]
    def save(self,*a,**k):
        if self.is_active and not self.published_at: self.published_at=timezone.now()
        super().save(*a,**k)
        if self.is_active:
            type(self).objects.exclude(pk=self.pk).update(is_active=False)
    def __str__(self): return self.version

class TermsAcceptance(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='terms_acceptances')
    terms=models.ForeignKey(TermsAndConditions,on_delete=models.PROTECT,related_name='acceptances')
    commission_rate=models.DecimalField(max_digits=5, decimal_places=2)
    accepted_at=models.DateTimeField(auto_now_add=True)
    ip_address=models.GenericIPAddressField(null=True, blank=True)
    class Meta:
        unique_together=[('user','terms')]

class PlatformSetting(models.Model):
    key=models.CharField(max_length=100, unique=True)
    value=models.CharField(max_length=500)
    description=models.TextField(blank=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        permissions=[('manage_settings','Can manage platform settings')]
    def __str__(self): return self.key

class Notification(models.Model):
    EVENT_CHOICES=[('provider_submitted','Provider submitted'),('provider_verified','Provider verified'),('provider_rejected','Provider rejected'),('documents_requested','Documents requested'),('new_order','New order'),('order_accepted','Order accepted'),('order_rejected','Order rejected'),('payment_successful','Payment successful'),('payment_failed','Payment failed'),('order_started','Order started'),('order_delivered','Order delivered'),('order_completed','Order completed'),('new_review','New review')]
    recipient=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='notifications')
    event_type=models.CharField(max_length=40, choices=EVENT_CHOICES, db_index=True)
    title=models.CharField(max_length=200)
    message=models.TextField()
    is_read=models.BooleanField(default=False, db_index=True)
    created_at=models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta: ordering=['-created_at']

class AuditLog(models.Model):
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='audit_logs')
    action=models.CharField(max_length=100, db_index=True)
    content_type=models.ForeignKey(ContentType,on_delete=models.SET_NULL,null=True,blank=True)
    object_id=models.CharField(max_length=64, blank=True)
    target=GenericForeignKey('content_type','object_id')
    metadata=models.JSONField(default=dict, blank=True)
    created_at=models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta: ordering=['-created_at']

def calculate_commission(gross_amount, commission_rate):
    gross=Decimal(gross_amount)
    rate=Decimal(commission_rate)
    commission=(gross*rate/Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return {'gross_amount':gross,'commission_rate':rate,'commission_amount':commission,'provider_net_amount':gross-commission}
