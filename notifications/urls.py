from django.urls import path
from . import views

urlpatterns = [
    path('exports/', views.export_jobs_api, name='export_jobs_api'),
]
