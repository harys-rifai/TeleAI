import json
import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import WeatherLocation

def resolve_coordinates(location_name):
    """
    Geocode location using free Open-Meteo Geocoding API.
    """
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(location_name)}&count=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = data.get('results', [])
            if results:
                loc = results[0]
                return loc.get('latitude'), loc.get('longitude'), loc.get('name')
    except Exception as e:
        print(f"[Geocoding Error] Failed to resolve coordinates: {e}")
    return None, None, location_name

def fetch_weather_report(lat, lon, location_name):
    """
    Fetch weather details using OpenWeather or Open-Meteo API.
    """
    from django.conf import settings
    api_key = settings.OPENWEATHER_API_KEY
    if api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                humidity = data['main']['humidity']
                return f"☀️ Weather Report for {location_name}:\n- Temp: {temp}°C\n- Status: {desc.capitalize()}\n- Humidity: {humidity}%"
        except Exception as e:
            print(f"[Weather Task] OpenWeather error: {e}, falling back to Open-Meteo")

    # Fallback to free Open-Meteo (No key required)
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            cw = data.get('current_weather', {})
            temp = cw.get('temperature', 'N/A')
            wind = cw.get('windspeed', 'N/A')
            code = cw.get('weathercode', 0)
            
            # Map weather codes
            weather_descriptions = {
                0: "Clear sky ☀️",
                1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
                45: "Foggy 🌫️", 48: "Depositing rime fog 🌫️",
                51: "Light drizzle 🌧️", 53: "Moderate drizzle 🌧️", 55: "Dense drizzle 🌧️",
                61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
                71: "Slight snow fall ❄️", 73: "Moderate snow fall ❄️", 75: "Heavy snow fall ❄️",
                80: "Slight rain showers 🌦️", 81: "Moderate rain showers 🌦️", 82: "Violent rain showers 🌦️",
                95: "Thunderstorm ⛈️"
            }
            desc = weather_descriptions.get(code, "Cloudy ☁️")
            return f"☀️ Weather Report for {location_name} (via Open-Meteo):\n- Temp: {temp}°C\n- Status: {desc}\n- Wind: {wind} km/h"
    except Exception as e:
        print(f"[Weather Task] Open-Meteo error: {e}")
        
    return f"⚠️ Weather Alert:\nCould not fetch weather updates for {location_name} at this time."

@login_required
@require_http_methods(["GET", "POST"])
def weather_locations_list(request):
    user = request.user
    
    if request.method == "GET":
        if user.is_admin:
            queryset = WeatherLocation.objects.all().select_related('user')
        else:
            queryset = WeatherLocation.objects.filter(user=user)
        
        # Pagination parameters
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
        except ValueError:
            page = 1
            page_size = 10
        
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        locations = queryset[(page - 1) * page_size:page * page_size]
            
        data = [{
            'id': loc.id,
            'user_email': loc.user.email,
            'location_name': loc.location_name,
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'target_chat_id': loc.target_chat_id,
            'schedule_time': loc.schedule_time.strftime('%H:%M'),
            'is_active': loc.is_active
        } for loc in locations]
        return JsonResponse({
            'success': True, 
            'locations': data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': total_pages
            }
        })
        
    elif request.method == "POST":
        if user.is_viewer:
            return JsonResponse({'success': False, 'error': 'Viewer role cannot configure weather locations.'}, status=403)
            
        try:
            body = json.loads(request.body)
            location_name = body.get('location_name', '').strip()
            target_chat_id = body.get('target_chat_id', '').strip()
            schedule_time_str = body.get('schedule_time', '08:00').strip()
            
            if not location_name or not target_chat_id:
                return JsonResponse({'success': False, 'error': 'location_name and target_chat_id are required.'})
                
            # Geocode coordinates
            lat, lon, resolved_name = resolve_coordinates(location_name)
            if lat is None or lon is None:
                # If geocoding failed, use defaults or prompt user
                return JsonResponse({'success': False, 'error': f"Could not find coordinates for '{location_name}'. please try another city name."})
                
            location = WeatherLocation.objects.create(
                user=user,
                location_name=resolved_name,
                latitude=lat,
                longitude=lon,
                target_chat_id=target_chat_id,
                schedule_time=schedule_time_str,
                is_active=True
            )
            return JsonResponse({
                'success': True,
                'message': f"Added weather updates for '{resolved_name}' ({lat:.4f}, {lon:.4f}) scheduled at {schedule_time_str}.",
                'location': {
                    'id': location.id,
                    'location_name': location.location_name,
                    'schedule_time': schedule_time_str
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["PUT", "DELETE"])
def weather_location_detail(request, pk):
    user = request.user
    if user.is_viewer:
        return JsonResponse({'success': False, 'error': 'Viewer role cannot modify weather configurations.'}, status=403)
        
    if user.is_admin:
        location = get_object_or_404(WeatherLocation, pk=pk)
    else:
        location = get_object_or_404(WeatherLocation, pk=pk, user=user)
        
    if request.method == "DELETE":
        location.delete()
        return JsonResponse({'success': True, 'message': 'Weather location removed.'})
        
    elif request.method == "PUT":
        try:
            body = json.loads(request.body)
            action = body.get('action') # 'toggle' or 'update' or 'realtime'
            
            if action == 'toggle':
                location.is_active = not location.is_active
                location.save()
                status_str = "activated" if location.is_active else "deactivated"
                return JsonResponse({'success': True, 'message': f'Weather bot {status_str} for {location.location_name}.'})
            elif action == 'realtime':
                weather_msg = fetch_weather_report(location.latitude, location.longitude, location.location_name)
                return JsonResponse({'success': True, 'message': weather_msg})
            else:
                location.location_name = body.get('location_name', location.location_name).strip()
                location.schedule_time = body.get('schedule_time', location.schedule_time.strftime('%H:%M')).strip()
                location.target_chat_id = body.get('target_chat_id', location.target_chat_id).strip()
                
                # Re-geocode if name changed
                if 'location_name' in body:
                    lat, lon, resolved_name = resolve_coordinates(location.location_name)
                    if lat is not None and lon is not None:
                        location.latitude = lat
                        location.longitude = lon
                        location.location_name = resolved_name
                        
                location.save()
                return JsonResponse({'success': True, 'message': 'Weather configuration updated.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
