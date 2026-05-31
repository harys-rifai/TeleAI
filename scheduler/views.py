import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from croniter import croniter
from telegram.models import TelegramAccount
from .models import ScheduledMessage

@login_required
@require_http_methods(["GET", "POST"])
def scheduled_messages_list(request):
    user = request.user
    
    if request.method == "GET":
        if user.is_admin:
            queryset = ScheduledMessage.objects.all().select_related('telegram_account', 'user')
        else:
            queryset = ScheduledMessage.objects.filter(user=user).select_related('telegram_account')
        
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
        
        schedules = queryset[(page - 1) * page_size:page * page_size]
            
        data = [{
            'id': s.id,
            'user_email': s.user.email,
            'phone_number': s.telegram_account.phone_number,
            'telegram_account_id': s.telegram_account.id,
            'target_chat_id': s.target_chat_id,
            'message_text': s.message_text,
            'schedule_type': s.schedule_type,
            'interval_seconds': s.interval_seconds,
            'cron_expression': s.cron_expression,
            'latitude': s.latitude,
            'longitude': s.longitude,
            'location_name': s.location_name,
            'status': s.status,
            'next_run_at': s.next_run_at.strftime('%Y-%m-%d %H:%M:%S') if s.next_run_at else "",
            'last_run_at': s.last_run_at.strftime('%Y-%m-%d %H:%M:%S') if s.last_run_at else ""
        } for s in schedules]
        return JsonResponse({
            'success': True, 
            'schedules': data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': total_pages
            }
        })
        
    elif request.method == "POST":
        if user.is_viewer:
            return JsonResponse({'success': False, 'error': 'Viewer role cannot create schedules.'}, status=403)
            
        try:
            body = json.loads(request.body)
            telegram_account_id = int(body.get('telegram_account_id'))
            target_chat_id = body.get('target_chat_id', '').strip()
            message_text = body.get('message_text', '').strip()
            schedule_type = body.get('schedule_type', 'once')
            interval_seconds = int(body.get('interval_seconds', 60))
            cron_expression = body.get('cron_expression', '').strip()
            
            # Retrieve account and verify access
            if user.is_admin:
                account = get_object_or_404(TelegramAccount, pk=telegram_account_id)
            else:
                account = get_object_or_404(TelegramAccount, pk=telegram_account_id, user=user)
                
            if not target_chat_id or not message_text:
                return JsonResponse({'success': False, 'error': 'target_chat_id and message_text are required.'})
                
            # Validate cron expression if cron type
            next_run = timezone.now()
            if schedule_type == ScheduledMessage.ScheduleType.CRON:
                if not cron_expression:
                    return JsonResponse({'success': False, 'error': 'cron_expression is required for Cron schedule.'})
                try:
                    iter_cron = croniter(cron_expression, timezone.now())
                    next_run = iter_cron.get_next(timezone.datetime)
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Invalid cron expression: {str(e)}'})
            elif schedule_type == ScheduledMessage.ScheduleType.INTERVAL:
                if interval_seconds < 10:
                    return JsonResponse({'success': False, 'error': 'Interval must be at least 10 seconds.'})
                next_run = timezone.now() + timezone.timedelta(seconds=interval_seconds)
            else:
                # Once
                next_run = timezone.now()
                
            schedule = ScheduledMessage.objects.create(
                user=user if not user.is_admin else account.user,  # associate with the account owner
                telegram_account=account,
                target_chat_id=target_chat_id,
                message_text=message_text,
                schedule_type=schedule_type,
                interval_seconds=interval_seconds,
                cron_expression=cron_expression if schedule_type == ScheduledMessage.ScheduleType.CRON else None,
                next_run_at=next_run,
                status=ScheduledMessage.Status.ACTIVE
            )
            
            return JsonResponse({'success': True, 'message': 'Message scheduled successfully.', 'id': schedule.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["PUT", "DELETE"])
def scheduled_message_detail(request, pk):
    user = request.user
    if user.is_viewer:
        return JsonResponse({'success': False, 'error': 'Viewer role cannot modify schedules.'}, status=403)
        
    if user.is_admin:
        schedule = get_object_or_404(ScheduledMessage, pk=pk)
    else:
        schedule = get_object_or_404(ScheduledMessage, pk=pk, user=user)
        
    if request.method == "DELETE":
        schedule.delete()
        return JsonResponse({'success': True, 'message': 'Schedule deleted successfully.'})
        
    elif request.method == "PUT":
        try:
            body = json.loads(request.body)
            action = body.get('action') # 'pause', 'resume', 'trigger'
            
            if action == 'pause':
                schedule.status = ScheduledMessage.Status.PAUSED
                schedule.save()
                return JsonResponse({'success': True, 'message': 'Schedule paused.'})
            elif action == 'resume':
                schedule.status = ScheduledMessage.Status.ACTIVE
                # Recalculate next run
                if schedule.schedule_type == ScheduledMessage.ScheduleType.CRON:
                    iter_cron = croniter(schedule.cron_expression, timezone.now())
                    schedule.next_run_at = iter_cron.get_next(timezone.datetime)
                elif schedule.schedule_type == ScheduledMessage.ScheduleType.INTERVAL:
                    schedule.next_run_at = timezone.now() + timezone.timedelta(seconds=schedule.interval_seconds)
                else:
                    schedule.next_run_at = timezone.now()
                schedule.save()
                return JsonResponse({'success': True, 'message': 'Schedule resumed.'})
            elif action == 'trigger':
                # Force trigger now (will be run by a task or synchronously)
                schedule.next_run_at = timezone.now()
                schedule.save()
                return JsonResponse({'success': True, 'message': 'Schedule scheduled for immediate execution.'})
            else:
                return JsonResponse({'success': False, 'error': 'Unknown action.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
