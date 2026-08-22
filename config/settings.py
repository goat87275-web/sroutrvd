"""
ملف إعدادات Django الرئيسي لمشروع منصة سوق الخدمات
Django settings for service_marketplace project.
"""

from pathlib import Path
from decouple import config
import importlib.util

# بناء المسارات داخل المشروع
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# إعدادات الأمان
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-temporary-key-change-in-production')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')


# تعريف التطبيقات المثبتة
# Application definition

INSTALLED_APPS = [
    # Jazzmin added conditionally below when installed

    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'crispy_forms',
    'crispy_bootstrap5',

    # Local apps
    'apps.accounts',
    'apps.marketplace',
    'apps.orders',
    'apps.reviews',
    'apps.chat',
    'apps.core',
    'apps.payments',
]

if importlib.util.find_spec('jazzmin'):
    INSTALLED_APPS.insert(0, 'jazzmin')

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # للملفات الثابتة
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.maps_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# إعدادات قاعدة البيانات
# Database configuration
# يستخدم SQLite افتراضياً، يمكن استخدام PostgreSQL من خلال .env

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# يمكن استخدام dj-database-url لاحقاً للإنتاج
# import dj_database_url
# DATABASES['default'] = dj_database_url.parse(config('DATABASE_URL'))


# التحقق من كلمة المرور
# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# الإعدادات الدولية
# Internationalization

LANGUAGE_CODE = 'ar'  # اللغة العربية
TIME_ZONE = 'Asia/Aden'  # التوقيت اليمني
USE_I18N = True
USE_TZ = True


# إعدادات الملفات الثابتة (CSS, JavaScript, Images)
# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# إعدادات الوسائط (الصور المرفوعة)
# Media files (uploaded by users)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
PRIVATE_MEDIA_ROOT = BASE_DIR / 'private_media'
MAX_PROVIDER_DOCUMENT_SIZE = 5 * 1024 * 1024
MAX_PAYMENT_PROOF_SIZE = 5 * 1024 * 1024
MAPS_API_KEY = config('MAPS_API_KEY', default='')


# إعدادات Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# نوع الحقل الافتراضي للمفاتيح الأساسية
# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# إعدادات الرسائل
# Messages framework settings
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}


# إعدادات البريد الإلكتروني
# Email settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')


# URL لإعادة التوجيه بعد تسجيل الدخول/الخروج
# Login/Logout redirects
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'


# ================================
# إعدادات Jazzmin - تصميم لوحة التحكم
# ================================

JAZZMIN_SETTINGS = {
    # عنوان الموقع
    'site_title': 'سوق الخدمات',
    'site_header': 'لوحة تحكم سوق الخدمات',
    'site_brand': 'سوق الخدمات',
    'site_logo_classes': 'img-circle',

    # رسالة الترحيب
    'welcome_sign': 'مرحباً بك في لوحة التحكم',
    'copyright': 'منصة سوق الخدمات © 2026',

    # البحث
    'search_model': ['accounts.User', 'marketplace.Service', 'orders.Order'],

    # المستخدم
    'user_avatar': None,

    ############
    # القائمة العلوية
    ############
    'topmenu_links': [
        {'name': 'الرئيسية', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'عرض الموقع', 'url': '/', 'new_window': True},
        {'model': 'accounts.User'},
    ],

    ############
    # القائمة الجانبية
    ############
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],

    # ترتيب التطبيقات والموديلات
    'order_with_respect_to': [
        'accounts',
        'marketplace',
        'orders',
        'reviews',
        'chat',
    ],

    # أيقونات التطبيقات والموديلات
    'icons': {
        'auth': 'fas fa-users-cog',
        'auth.group': 'fas fa-users',
        'accounts': 'fas fa-user-shield',
        'accounts.user': 'fas fa-users',
        'accounts.providerprofile': 'fas fa-id-badge',
        'marketplace': 'fas fa-store',
        'marketplace.category': 'fas fa-th-large',
        'marketplace.service': 'fas fa-concierge-bell',
        'orders': 'fas fa-shopping-cart',
        'orders.order': 'fas fa-file-invoice',
        # 'orders.milestone': 'fas fa-tasks', # مجمد مؤقتاً
        'orders.delivery': 'fas fa-truck',
        'orders.ordermessage': 'fas fa-comment-dots',
        'reviews': 'fas fa-star',
        'reviews.review': 'fas fa-star-half-alt',
        'chat': 'fas fa-comments',
        'chat.conversation': 'fas fa-comment-alt',
        'chat.message': 'fas fa-envelope',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',

    ############
    # واجهة المستخدم
    ############
    'related_modal_active': True,
    'custom_css': None,
    'custom_js': None,
    'use_google_fonts_cdn': True,
    'show_ui_builder': False,
    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {
        'accounts.user': 'collapsible',
        'marketplace.service': 'horizontal_tabs',
        'orders.order': 'horizontal_tabs',
    },
    'language_chooser': False,
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': False,
    'accent': 'accent-primary',
    'navbar': 'navbar-white navbar-light',
    'no_navbar_border': False,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-primary',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'default',
    'dark_mode_theme': 'darkly',
    'button_classes': {
        'primary': 'btn-outline-primary',
        'secondary': 'btn-outline-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
    'actions_sticky_top': True,
}

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
