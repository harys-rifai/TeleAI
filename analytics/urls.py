from django.urls import path
from . import views

urlpatterns = [
    path('metrics/', views.analytics_metrics, name='analytics_metrics'),
]
