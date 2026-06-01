from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.message_logs_list, name='message_logs_list'),
]
