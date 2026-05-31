from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from telegram.models import TelegramAccount
from messaging.models import MessageLog
from scheduler.models import ScheduledMessage
from weather.models import WeatherLocation
from notifications.models import ExportJob

@login_required
def dashboard_home(request):
    """
    Render main dashboard template.
    """
    return render(request, 'dashboard/index.html')

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
    
    active_weather = weather_bots.filter(is_active=True).count()
    total_exports = exports.count()
    
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
                'total': weather_bots.count()
            },
            'exports': total_exports
        }
    })
