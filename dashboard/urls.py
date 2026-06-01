from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('dashboard/', views.dashboard_home, name='dashboard_home_alt'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('weather-info/', views.weather_info_page, name='weather_info'),
    
    # API endpoints
    path('dashboard/api/stats/', views.api_stats, name='dashboard_api_stats'),
    path('dashboard/api/weather-current/', views.api_weather_current, name='api_weather_current'),
]
