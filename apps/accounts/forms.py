"""
نماذج تسجيل الدخول والتسجيل
Forms for login, registration, and profile editing
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
from .models import User, ProviderProfile, ProviderDocument


# تعريف أداة التحقق من رقم الهاتف (أرقام فقط، ومتاح إشارة + اختياريًا)
phone_validator = RegexValidator(
    regex=r'^\+?[0-9]{8,15}$',
    message="يرجى إدخال رقم هاتف صحيح يحتوي على أرقام فقط (مثال: 771234567)."
)


class UserRegisterForm(UserCreationForm):
    """
    نموذج تسجيل مستخدم جديد
    User registration form
    """
    email = forms.EmailField(
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@domain.com'
        })
    )
    
    phone = forms.CharField(
        label='رقم الجوال',
        required=False,
        validators=[phone_validator],  # تم إضافة الفلتر هنا
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '77XXXXXXX',
            'type': 'tel',
            'inputmode': 'numeric',
            'oninput': "this.value = this.value.replace(/[^0-9+]/g, '')"  # يمنع الحروف مباشرة أثناء الطباعة
        })
    )
    
    city = forms.CharField(
        label='المدينة',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'صنعاء'
        })
    )
    
    role = forms.ChoiceField(
        label='نوع الحساب',
        choices=[('customer', 'عميل'), ('provider', 'مقدم خدمة')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='customer'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'city', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المستخدم'
            }),
        }
        labels = {
            'username': 'اسم المستخدم',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'كلمة المرور'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'تأكيد كلمة المرور'
        })
        self.fields['password1'].label = 'كلمة المرور'
        self.fields['password2'].label = 'تأكيد كلمة المرور'
    
    def clean_email(self):
        """التحقق من عدم تكرار البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل.')
        return email

    def clean_phone(self):
        """التحقق من رقم الهاتف لمنع كتابة الحروف"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # التأكد من إزالة أي مسافات زائدة
            phone = phone.strip()
            # التأكد أن القيمة تحتوي على أرقام فقط
            if not phone.isdigit() and not phone.startswith('+'):
                raise ValidationError('يجب أن يحتوي رقم الجوال على أرقام فقط.')
        return phone


class UserLoginForm(AuthenticationForm):
    """
    نموذج تسجيل الدخول
    Login form
    """
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المستخدم',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'كلمة المرور'
        })
    )


class UserProfileForm(forms.ModelForm):
    """
    نموذج تعديل الملف الشخصي الأساسي
    User profile edit form
    """
    phone = forms.CharField(
        label='رقم الجوال',
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '77XXXXXXX',
            'type': 'tel',
            'inputmode': 'numeric',
            'oninput': "this.value = this.value.replace(/[^0-9+]/g, '')"
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'city']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الأول'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم العائلة'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة'}),
        }
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الجوال',
            'city': 'المدينة',
        }
    
    def clean_email(self):
        """التحقق من عدم تكرار البريد الإلكتروني عند التعديل"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل.')
        return email

    def clean_phone(self):
        """التحقق من رقم الهاتف عند التعديل"""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            if not phone.isdigit() and not phone.startswith('+'):
                raise ValidationError('يجب أن يحتوي رقم الجوال على أرقام فقط.')
        return phone


class ProviderProfileForm(forms.ModelForm):
    """
    نموذج تعديل ملف مقدم الخدمة
    Provider profile edit form
    """
    phone = forms.CharField(label='هاتف العمل', required=False, validators=[phone_validator], widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '77XXXXXXX', 'type': 'tel', 'inputmode': 'numeric'}))
    latitude = forms.DecimalField(label='خط العرض', required=False, max_digits=9, decimal_places=6, min_value=-90, max_value=90, widget=forms.HiddenInput())
    longitude = forms.DecimalField(label='خط الطول', required=False, max_digits=9, decimal_places=6, min_value=-180, max_value=180, widget=forms.HiddenInput())

    class Meta:
        model = ProviderProfile
        fields = ['business_name','display_name','bio','phone','email','profile_image','specialization','experience_years','qualifications','experience','hourly_rate','address','city','district','latitude','longitude','service_radius','availability','is_available']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'اكتب نبذة تعريفية عنك وعن خبراتك...'
            }),
            'business_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم النشاط التجاري'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الظاهر للعملاء'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'هاتف العمل'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'business@example.com'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: تصميم جرافيك'
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '5'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '100.00'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'العنوان التفصيلي...'
            }),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الحي / المنطقة'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'service_radius': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'availability': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: السبت - الخميس 9ص إلى 5م'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'business_name': 'اسم النشاط',
            'display_name': 'اسم العرض',
            'phone': 'هاتف العمل',
            'email': 'بريد العمل',
            'bio': 'نبذة تعريفية',
            'profile_image': 'صورة الملف الشخصي',
            'specialization': 'التخصص',
            'experience_years': 'سنوات الخبرة',
            'hourly_rate': 'السعر بالساعة (ريال يمني)',
            'qualifications': 'المؤهلات',
            'experience': 'الخبرات',
            'address': 'العنوان',
            'city': 'مدينة العمل',
            'district': 'المنطقة / الحي',
            'service_radius': 'نطاق الخدمة (كم)',
            'availability': 'التوفر',
            'is_available': 'متاح لطلبات جديدة',
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        if (latitude is None) ^ (longitude is None):
            raise ValidationError('يجب تحديد خط العرض وخط الطول معًا أو تركهما فارغين.')
        return cleaned_data

class ProviderDocumentForm(forms.ModelForm):
    class Meta:
        model = ProviderDocument
        fields = ['document_type','file']
        widgets = {'document_type': forms.Select(attrs={'class':'form-select'}), 'file': forms.FileInput(attrs={'class':'form-control'})}
    def clean_file(self):
        f=self.cleaned_data['file']
        allowed_ext={'.pdf','.jpg','.jpeg','.png','.doc','.docx'}
        allowed_mimes={'application/pdf','image/jpeg','image/png','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        import os
        ext=os.path.splitext(f.name.lower())[1]
        content_type=getattr(f, 'content_type', '')
        if ext not in allowed_ext: raise ValidationError('نوع الملف غير مسموح.')
        if content_type and content_type not in allowed_mimes: raise ValidationError('نوع MIME غير مسموح.')
        if f.size > getattr(settings, 'MAX_PROVIDER_DOCUMENT_SIZE', 5*1024*1024): raise ValidationError('حجم الملف يتجاوز 5MB.')
        if ext in {'.exe','.bat','.sh','.js'}: raise ValidationError('الملفات التنفيذية ممنوعة.')
        return f
