from django.urls import path
from . import views

urlpatterns = [
    path('configs/', views.ai_config_api, name='ai_config_api'),
    path('test-prompt/', views.ai_test_prompt, name='ai_test_prompt'),
]
