from django.urls import path
from . import views, views_admin

urlpatterns = [
    path('signup/', views.signup_view, name='account_signup'),
    path('login/', views.login_view, name='account_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bills/', views.bills, name='bills'),
    path('usage/', views.usage, name='usage'),
    path('payments/', views.payments, name='payments'),
    path('payment-method-selection/', views.payment_method_selection, name='payment_method_selection'),
    path('ewallet-payment/', views.ewallet_payment, name='ewallet_payment'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Add path for admin dashboard
    path('admin/dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),  
    path('admin/paid-consumers/', views_admin.paid_consumers, name='paid_consumers'),
    path('admin/billing_management/', views_admin.input_water_reading, name='billing_management'),  
    path('admin/verify_payments/', views_admin.verify_payments, name='verify_payments'),  
    path('admin/settings/', views_admin.admin_settings, name='admin_settings'),  
]
