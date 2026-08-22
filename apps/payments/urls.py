from django.urls import path
from . import views
app_name='payments'
urlpatterns=[
    path('create/<str:order_number>/', views.payment_create, name='payment_create'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
    path('<int:pk>/proof/', views.payment_submit_proof, name='payment_submit_proof'),
    path('<int:pk>/approve/', views.payment_approve, name='payment_approve'),
    path('<int:pk>/reject/', views.payment_reject, name='payment_reject'),
    path('<int:pk>/test-success/', views.payment_test_success, name='payment_test_success'),
    path('<int:pk>/test-fail/', views.payment_test_fail, name='payment_test_fail'),
]
