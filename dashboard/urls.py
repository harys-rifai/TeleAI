from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('dashboard/', views.dashboard_home, name='dashboard_home_alt'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints
    path('dashboard/api/stats/', views.api_stats, name='dashboard_api_stats'),
]
