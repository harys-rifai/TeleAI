from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.views.decorators.cache import never_cache
import requests
from telegram.models import TelegramAccount
from messaging.models import MessageLog
from scheduler.models import ScheduledMessage
from weather.models import WeatherLocation
from weather.utils import map_weather_code, resolve_coordinates
from notifications.models import ExportJob

@login_required
@never_cache
def weather_info_page(request):
    return render(request, 'dashboard/weather_info.html', {
        'WEATHER_API_KEY': getattr(settings, 'WEATHER_API_KEY', '')
    })

@login_required
@require_http_methods(["GET"])
def api_weather_current(request):
    city = request.GET.get('q', 'Jakarta')
    
    try:
        lat, lon, resolved_name = resolve_coordinates(city)
        if lat is None or lon is None:
            return JsonResponse({'success': False, 'error': f'City "{city}" not found'}, status=400)
        
        # Use detailed current parameters
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,surface_pressure,wind_speed_10m,visibility&timezone=auto")
        weather_res = requests.get(weather_url, timeout=10)
        if weather_res.status_code != 200:
            return JsonResponse({'success': False, 'error': 'Weather API failed'}, status=400)
        
        res_json = weather_res.json()
        current = res_json.get('current', {})
        if not current:
            return JsonResponse({'success': False, 'error': 'No current weather data available from provider'}, status=404)
        
        # Safe temperature conversion
        temp_c = current.get('temperature_2m', 0)
        try:
            temp_f = round(float(temp_c or 0) * 1.8 + 32, 1)
        except (ValueError, TypeError):
            temp_f = 'N/A'
        
        response_data = {
            'location': {
                'name': resolved_name or city,
                'region': 'Detected',
                'country': '',
                'lat': lat,
                'lon': lon
            },
            'current': {
                'temp_c': temp_c,
                'temp_f': temp_f,
                'wind_kph': current.get('wind_speed_10m', 'N/A'),
                'wind_km': current.get('wind_speed_10m', 0),
                'wind_dir': 'N/A',
                'wind_degree': 0,
                'pressure_mb': current.get('surface_pressure', 'N/A'),
                'humidity': current.get('relative_humidity_2m', 'N/A'),
                'vis_km': round(float(current.get('visibility', 0)) / 1000, 1) if current.get('visibility') else 'N/A',
                'cloud': 'N/A',
                'uv': 'N/A',
                'condition': {
                    'text': map_weather_code(current.get('weather_code', 0)),
                    'icon': '//cdn.weatherapi.com/weather/64x64/day/116.png',
                    'code': current.get('weather_code', 0)
                },
                'last_updated': 'now',
                'feelslike_c': current.get('apparent_temperature', 'N/A'),
                'gust_kph': 'N/A',
                'air_quality': {
                    'co': 'N/A', 'no2': 'N/A', 'o3': 'N/A', 'so2': 'N/A',
                    'pm2_5': 'N/A', 'pm10': 'N/A', 'us-epa-index': 0, 'gb-defra-index': 0
                },
                'chance_of_rain': 0,
                'precip_mm': 0
            }
        }
        return JsonResponse({'success': True, 'data': response_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def dashboard_home(request):
    """
    Render main dashboard template.
    """
    return render(request, 'dashboard/index.html', {
        'firebase_api_key': settings.FIREBASE_API_KEY or ''
    })

def login_view(request):
    """
    Handle user login.
    """
    if request.user.is_authenticated:
        return redirect('dashboard_home')
        
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard_home')
        else:
            error = "Invalid email or password."
            
    return render(request, 'dashboard/login.html', {'error': error})

def logout_view(request):
    """
    Handle user logout.
    """
    logout(request)
    return redirect('login')

@login_required
@require_http_methods(["GET"])
def api_stats(request):
    """
    API endpoint returning statistics cards summary numbers.
    """
    user = request.user
    
    # Filter base objects depending on Role
    if user.is_admin:
        accounts = TelegramAccount.objects.all()
        logs = MessageLog.objects.all()
        schedules = ScheduledMessage.objects.all()
        weather_bots = WeatherLocation.objects.all()
        exports = ExportJob.objects.all()
    else:
        accounts = TelegramAccount.objects.filter(user=user)
        logs = MessageLog.objects.filter(user=user)
        schedules = ScheduledMessage.objects.filter(user=user)
        weather_bots = WeatherLocation.objects.filter(user=user)
        exports = ExportJob.objects.filter(user=user)
        
    total_accounts = accounts.count()
    active_accounts = accounts.filter(is_active=True).count()
    
    total_sent = logs.filter(direction=MessageLog.Direction.OUTBOUND, status=MessageLog.Status.SUCCESS).count()
    failed_sent = logs.filter(direction=MessageLog.Direction.OUTBOUND, status=MessageLog.Status.FAILED).count()
    total_received = logs.filter(direction=MessageLog.Direction.INBOUND).count()
    
    active_schedules = schedules.filter(status=ScheduledMessage.Status.ACTIVE).count()
    completed_schedules = schedules.filter(status=ScheduledMessage.Status.COMPLETED).count()
    
    try:
        active_weather = weather_bots.filter(is_active=True).count()
        total_weather = weather_bots.count()
    except Exception:
        active_weather = 0
        total_weather = 0
    
    # Prepare historical data for graphs (outbound vs inbound over last 7 days)
    # Simple mockup stats if logs database is sparse, or compute based on dates.
    # We will build a basic array of labels and data.
    return JsonResponse({
        'success': True,
        'stats': {
            'accounts': {
                'total': total_accounts,
                'active': active_accounts,
            },
            'messages': {
                'sent': total_sent,
                'failed': failed_sent,
                'received': total_received,
            },
            'schedules': {
                'active': active_schedules,
                'completed': completed_schedules,
                'total': schedules.count()
            },
            'weather': {
                'active': active_weather,
                'total': total_weather
            },
            'exports': exports.count()
        }
    })
