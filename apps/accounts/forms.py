"""
نماذج تسجيل الدخول والتسجيل
Forms for login, registration, and profile editing
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
from .models import User, ProviderProfile, ProviderDocument, ProviderVerificationRequest
from apps.core.models import City, District
from apps.marketplace.models import ManagedService, Specialization, Qualification


class LocationFieldsMixin:
    """Restrict district choices on both initial rendering and forged POSTs."""
    def configure_location_fields(self):
        self.fields['location_city'].queryset = City.objects.filter(is_active=True)
        city_id = self.data.get(self.add_prefix('location_city')) or getattr(self.instance, 'location_city_id', None)
        self.fields['location_district'].queryset = District.objects.filter(is_active=True, city_id=city_id) if city_id else District.objects.none()

    def clean_location_district(self):
        district = self.cleaned_data.get('location_district')
        city = self.cleaned_data.get('location_city')
        if district and (not city or district.city_id != city.id):
            raise ValidationError('اختر مديرية تابعة للمدينة المختارة.')
        return district


# تعريف أداة التحقق من رقم الهاتف (أرقام فقط، ومتاح إشارة + اختياريًا)
phone_validator = RegexValidator(
    regex=r'^\+?[0-9]{8,15}$',
    message="يرجى إدخال رقم هاتف صحيح يحتوي على أرقام فقط (مثال: 771234567)."
)


class UserRegisterForm(LocationFieldsMixin, UserCreationForm):
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
    
    
    role = forms.ChoiceField(
        label='نوع الحساب',
        choices=[('customer', 'عميل'), ('provider', 'مقدم خدمة')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='customer'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'location_city', 'location_district', 'role', 'password1', 'password2']
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
        self.configure_location_fields()
    
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


class UserProfileForm(LocationFieldsMixin, forms.ModelForm):
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
        fields = ['first_name', 'last_name', 'email', 'phone', 'location_city', 'location_district']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الأول'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم العائلة'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'location_city': forms.Select(attrs={'class': 'form-select'}),
            'location_district': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الجوال',
            'location_city': 'المدينة', 'location_district': 'المديرية',
        }
    
    def clean_email(self):
        """التحقق من عدم تكرار البريد الإلكتروني عند التعديل"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل.')
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.configure_location_fields()

    def clean_phone(self):
        """التحقق من رقم الهاتف عند التعديل"""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            if not phone.isdigit() and not phone.startswith('+'):
                raise ValidationError('يجب أن يحتوي رقم الجوال على أرقام فقط.')
        return phone


class ProviderProfileForm(LocationFieldsMixin, forms.ModelForm):
    """
    نموذج تعديل ملف مقدم الخدمة
    Provider profile edit form
    """
    phone = forms.CharField(label='هاتف العمل', required=False, validators=[phone_validator], widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '77XXXXXXX', 'type': 'tel', 'inputmode': 'numeric'}))
    latitude = forms.DecimalField(label='خط العرض', required=False, max_digits=9, decimal_places=6, min_value=-90, max_value=90, widget=forms.HiddenInput())
    longitude = forms.DecimalField(label='خط الطول', required=False, max_digits=9, decimal_places=6, min_value=-180, max_value=180, widget=forms.HiddenInput())

    class Meta:
        model = ProviderProfile
        fields = ['business_name','display_name','bio','phone','email','profile_image','specializations','specialization','experience_years','qualification_choices','qualifications','experience','hourly_rate','address','location_city','location_district','city','district','latitude','longitude','service_radius','availability','is_available']
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
            'specializations': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'specialization': forms.HiddenInput(),
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
            'location_city': forms.Select(attrs={'class': 'form-select'}),
            'location_district': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.HiddenInput(), 'district': forms.HiddenInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'service_radius': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'availability': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: السبت - الخميس 9ص إلى 5م'}),
            'qualification_choices': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'qualifications': forms.HiddenInput(),
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
            'specializations': 'التخصصات',
            'experience_years': 'سنوات الخبرة',
            'hourly_rate': 'السعر بالساعة (ريال يمني)',
            'qualification_choices': 'المؤهلات',
            'experience': 'الخبرات',
            'address': 'العنوان',
            'location_city': 'مدينة العمل', 'location_district': 'المديرية',
            'service_radius': 'نطاق الخدمة (كم)',
            'availability': 'التوفر',
            'is_available': 'متاح لطلبات جديدة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure_location_fields()
        self.fields['specializations'].queryset = Specialization.objects.filter(is_active=True)
        self.fields['qualification_choices'].queryset = Qualification.objects.filter(is_active=True)

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


class ProviderVerificationRequestForm(forms.ModelForm):
    class Meta:
        model = ProviderVerificationRequest
        fields = ['requested_services']
        widgets = {'requested_services': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6})}

    def __init__(self, *args, provider=None, **kwargs):
        self.provider = provider
        super().__init__(*args, **kwargs)
        self.fields['requested_services'].queryset = ManagedService.objects.filter(is_active=True)

    def clean_requested_services(self):
        services = self.cleaned_data['requested_services']
        if not services:
            raise ValidationError('اختر خدمة أساسية واحدة على الأقل لطلب التوثيق.')
        return services
