from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Link authentication and front-end dashboard routes
    path('', include('dashboard.urls')),
    
    # API endpoints
    path('api/telegram/', include('telegram.urls')),
    path('api/messages/', include('messaging.urls')),
    path('api/scheduler/', include('scheduler.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/ai/', include('ai.urls')),
    path('api/weather/', include('weather.urls')),
    path('api/version/', include('version.urls')),
    path('api/notifications/', include('notifications.urls')),
]
