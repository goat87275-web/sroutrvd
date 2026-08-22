"""
URLs لتطبيق accounts
URL routing for accounts app
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path("provider/documents/", views.provider_documents_view, name="provider_documents"),
    path("provider/submit-review/", views.provider_submit_review, name="provider_submit_review"),
    path("provider/accept-commission/", views.accept_commission_policy, name="accept_commission_policy"),
    path("provider/documents/<int:pk>/download/", views.provider_document_download, name="provider_document_download"),
    # التسجيل وتسجيل الدخول
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # الملف الشخصي
    path('profile/', views.profile_view, name='profile'),
    
    # ملف مقدم الخدمة
    path('provider/edit/', views.provider_profile_edit_view, name='provider_profile_edit'),
    path('provider/<int:pk>/', views.ProviderDetailView.as_view(), name='provider_detail'),
]
