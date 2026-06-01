from celery import shared_task
from django.utils import timezone
from croniter import croniter
from telegram.models import TelegramAccount
from telegram.telethon_helper import send_message
from messaging.models import MessageLog
from analytics.clickhouse_client import log_message_event
from .models import ScheduledMessage
from datetime import timedelta

@shared_task
def send_scheduled_messages():
    """Process active scheduled messages due for delivery."""
    now = timezone.now()
    due_messages = ScheduledMessage.objects.filter(
        status=ScheduledMessage.Status.ACTIVE,
        next_run_at__lte=now + timezone.timedelta(seconds=5) # 5s buffer for beat lag
    ).select_related('telegram_account', 'user')

    for msg in due_messages:
        account = msg.telegram_account
        if not account or not account.is_active:
            continue

        # Execute sending
        res = send_message(
            session_string=account.session_string,
            api_id=account.api_id,
            api_hash=account.api_hash,
            target_chat=msg.target_chat_id,
            message_text=msg.message_text
        )

        success = res.get('success', False)
        status_log = MessageLog.Status.SUCCESS if success else MessageLog.Status.FAILED
        
        # Log Result
        MessageLog.objects.create(
            user=msg.user,
            telegram_account=account,
            chat_id=res.get('chat_id', msg.target_chat_id),
            chat_title=res.get('chat_title', 'Scheduled Task'),
            message_text=msg.message_text,
            direction=MessageLog.Direction.OUTBOUND,
            status=status_log
        )
        
        try:
            log_message_event(
                user_id=msg.user.id,
                account_id=account.id,
                direction='outbound',
                status='success' if success else 'failed',
                chat_id=res.get('chat_id', msg.target_chat_id),
                text=msg.message_text
            )
        except Exception: pass

        # Update Schedule state
        msg.last_run_at = now
        if msg.schedule_type == ScheduledMessage.ScheduleType.ONCE:
            msg.status = ScheduledMessage.Status.COMPLETED
        elif msg.schedule_type == ScheduledMessage.ScheduleType.INTERVAL:
            # Ensure we don't drift: calculate from intended next_run_at
            base_time = msg.next_run_at if msg.next_run_at > now - timedelta(minutes=1) else now
            msg.next_run_at = base_time + timedelta(seconds=msg.interval_seconds)
        elif msg.schedule_type == ScheduledMessage.ScheduleType.CRON:
            try:
                # Calculate the next occurrence from 'now' using the cron expression
                # Ensure we are using a localized datetime for croniter
                local_now = timezone.localtime(now)
                iter_cron = croniter(msg.cron_expression, local_now)
                msg.next_run_at = iter_cron.get_next(timezone.datetime)
            except Exception as e:
                print(f"[Scheduler Error] Invalid cron '{msg.cron_expression}': {e}")
                msg.status = ScheduledMessage.Status.PAUSED # Pause if expression is invalid
        
        msg.save()