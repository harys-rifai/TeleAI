from datetime import datetime
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import WeatherLocation
from .utils import resolve_coordinates, fetch_weather_report

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
                return JsonResponse({'success': False, 'error': f"Could not find coordinates for '{location_name}'. Please try another city name."})
                
            location = WeatherLocation.objects.create(
                user=user,
                location_name=resolved_name,
                latitude=lat,
                longitude=lon,
                target_chat_id=target_chat_id,
                schedule_time=datetime.strptime(schedule_time_str, '%H:%M').time(),
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
                if not location.latitude or not location.longitude:
                    lat, lon, _ = resolve_coordinates(location.location_name)
                    if lat:
                        location.latitude, location.longitude = lat, lon
                        location.save()
                    else:
                        return JsonResponse({'success': False, 'error': 'Invalid coordinates for this location.'})
                
                weather_msg = fetch_weather_report(location.latitude, location.longitude, location.location_name)
                return JsonResponse({'success': True, 'message': weather_msg})
            else:
                new_name = body.get('location_name', location.location_name).strip()
                schedule_time_str = body.get('schedule_time', location.schedule_time.strftime('%H:%M')).strip()
                try:
                    location.schedule_time = datetime.strptime(schedule_time_str, '%H:%M').time()
                except ValueError:
                    pass
                location.target_chat_id = body.get('target_chat_id', location.target_chat_id).strip()
                
                # Re-geocode if name changed or coordinates missing
                if new_name != location.location_name or not location.latitude:
                    lat, lon, resolved_name = resolve_coordinates(new_name)
                    if lat is not None and lon is not None:
                        location.latitude = lat
                        location.longitude = lon
                        location.location_name = resolved_name or new_name
                        
                location.save()
                return JsonResponse({'success': True, 'message': 'Weather configuration updated.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
