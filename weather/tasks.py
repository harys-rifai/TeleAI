from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.db import models
from django.utils import timezone
from telegram.models import TelegramAccount
from telegram.telethon_helper import send_message
from messaging.models import MessageLog
from analytics.clickhouse_client import log_message_event
from .models import WeatherLocation
from .utils import fetch_weather_report

@shared_task
def send_weather_updates():
    """
    Periodic task to send scheduled weather updates.
    """
    # Use Django's localized time instead of manual offset math
    now_local = timezone.localtime(timezone.now())
    
    # Select active weather tasks scheduled for this hour/minute
    # and ensure they haven't run in the last hour to prevent duplicates
    locations = WeatherLocation.objects.filter(
        is_active=True,
        schedule_time__hour=now_local.hour,
        schedule_time__minute=now_local.minute
    ).filter(
        models.Q(last_run_at__isnull=True) | 
        models.Q(last_run_at__lt=timezone.now() - timezone.timedelta(minutes=59))
    ).select_related('user')
    
    for loc in locations:
        # Get user active Telegram account
        account = TelegramAccount.objects.filter(user=loc.user, is_active=True).first()
        if not account or not account.session_string:
            continue
            
        weather_msg = fetch_weather_report(loc.latitude, loc.longitude, loc.location_name)
        
        # Send weather report
        res = send_message(
            session_string=account.session_string,
            api_id=account.api_id,
            api_hash=account.api_hash,
            target_chat=loc.target_chat_id,
            message_text=weather_msg
        )
        
        status_log = MessageLog.Status.SUCCESS if res.get('success') else MessageLog.Status.FAILED
        chat_title = res.get('chat_title', loc.target_chat_id)
        chat_id = res.get('chat_id', loc.target_chat_id)
        
        # Log to PostgreSQL
        MessageLog.objects.create(
            user=loc.user,
            telegram_account=account,
            chat_id=chat_id,
            chat_title=chat_title,
            message_text=weather_msg,
            direction=MessageLog.Direction.OUTBOUND,
            status=status_log
        )
        
        # Log to ClickHouse
        try:
            log_message_event(
                user_id=loc.user.id,
                account_id=account.id,
                direction='outbound',
                status='success' if res.get('success') else 'failed',
                chat_id=chat_id,
                text=weather_msg
            )
        except Exception:
            pass

        # Update last run time to prevent immediate re-runs
        loc.last_run_at = timezone.now()
        loc.save(update_fields=['last_run_at'])
