from django.urls import path
from . import views

urlpatterns = [
    path('accounts/', views.telegram_accounts_list, name='telegram_accounts_list'),
    path('accounts/<int:pk>/', views.delete_telegram_account, name='delete_telegram_account'),
    path('accounts/send-code/', views.send_auth_code, name='telegram_send_code'),
    path('accounts/verify-code/', views.verify_auth_code, name='telegram_verify_code'),
    path('accounts/verify-2fa/', views.verify_2fa_password, name='telegram_verify_2fa'),
]
