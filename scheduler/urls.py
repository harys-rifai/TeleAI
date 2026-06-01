from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.scheduled_messages_list, name='scheduled_messages_list'),
    path('messages/<int:pk>/', views.scheduled_message_detail, name='scheduled_message_detail'),
]
