import os
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import ProviderWallet, Payment, wallet_account_validator

class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['proof_file']
        widgets = {'proof_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/png,image/jpeg,application/pdf'})}
        labels = {'proof_file': 'سند الحوالة / إشعار التحويل'}
    def clean_proof_file(self):
        f=self.cleaned_data['proof_file']
        allowed_ext={'.pdf','.jpg','.jpeg','.png'}
        allowed_mimes={'application/pdf','image/jpeg','image/png'}
        ext=os.path.splitext(f.name.lower())[1]
        content_type=getattr(f, 'content_type', '')
        if ext not in allowed_ext: raise ValidationError('نوع الملف غير مسموح.')
        if content_type and content_type not in allowed_mimes: raise ValidationError('نوع MIME غير مسموح.')
        if f.size > getattr(settings, 'MAX_PAYMENT_PROOF_SIZE', 5*1024*1024): raise ValidationError('حجم الملف يتجاوز 5MB.')
        return f

class PaymentRejectForm(forms.Form):
    reason=forms.CharField(label='سبب الرفض', widget=forms.Textarea(attrs={'class':'form-control','rows':3}), min_length=3)

class ProviderWalletAccountForm(forms.ModelForm):
    class Meta:
        model=ProviderWallet
        fields=['account_number','is_active']
    def clean(self):
        data=super().clean()
        if data.get('is_active') and not data.get('account_number'):
            raise ValidationError('رقم الحساب مطلوب للمحفظة المفعلة.')
        return data
