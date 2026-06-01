from django.urls import path
from . import views

urlpatterns = [
    path('locations/', views.weather_locations_list, name='weather_locations_list'),
    path('locations/<int:pk>/', views.weather_location_detail, name='weather_location_detail'),
]
