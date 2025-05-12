from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='account_signup'),
    path('login/', views.login_view, name='account_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bills/', views.bills, name='bills'),
    path('usage/', views.usage, name='usage'),
    path('payments/', views.payments, name='payments'),
    path('payment-method-selection/', views.payment_method_selection,name='payment_method_selection'),
    path('settings/', views.settings_view, name='settings'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('logout/', views.custom_logout, name='logout'),
]
