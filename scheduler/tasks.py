from celery import shared_task
from django.utils import timezone
from croniter import croniter
from telegram.models import TelegramAccount
from telegram.telethon_helper import send_message
from messaging.models import MessageLog
from analytics.clickhouse_client import log_message_event
from .models import ScheduledMessage

@shared_task
def send_scheduled_messages():
    """
    Periodic task to send scheduled messages that are due.
    """
    now = timezone.now()
    due_schedules = ScheduledMessage.objects.filter(
        status=ScheduledMessage.Status.ACTIVE,
        next_run_at__lte=now
    ).select_related('telegram_account', 'user')

    for schedule in due_schedules:
        account = schedule.telegram_account
        if not account.is_active or not account.session_string:
            # Skip inactive accounts
            continue

        # Send message via Telethon helper
        result = send_message(
            session_string=account.session_string,
            api_id=account.api_id,
            api_hash=account.api_hash,
            target_chat=schedule.target_chat_id,
            message_text=schedule.message_text
        )

        log_status = MessageLog.Status.SUCCESS if result.get('success') else MessageLog.Status.FAILED
        chat_title = result.get('chat_title', schedule.target_chat_id)
        chat_id = result.get('chat_id', schedule.target_chat_id)

        # Create Postgres Message Log
        MessageLog.objects.create(
            user=schedule.user,
            telegram_account=account,
            chat_id=chat_id,
            chat_title=chat_title,
            message_text=schedule.message_text,
            direction=MessageLog.Direction.OUTBOUND,
            status=log_status,
            sent_at=now
        )

        # Clickhouse Analytics log (if ClickHouse is running, helper handles failures gracefully)
        try:
            log_message_event(
                user_id=schedule.user.id,
                account_id=account.id,
                direction='outbound',
                status='success' if result.get('success') else 'failed',
                chat_id=chat_id,
                text=schedule.message_text
            )
        except Exception:
            pass # ignore ClickHouse tracking failures in task thread

        # Update Schedule parameters
        schedule.last_run_at = now
        
        if schedule.schedule_type == ScheduledMessage.ScheduleType.ONCE:
            schedule.status = ScheduledMessage.Status.COMPLETED
            schedule.next_run_at = now
        elif schedule.schedule_type == ScheduledMessage.ScheduleType.INTERVAL:
            schedule.next_run_at = now + timezone.timedelta(seconds=schedule.interval_seconds)
        elif schedule.schedule_type == ScheduledMessage.ScheduleType.CRON:
            try:
                iter_cron = croniter(schedule.cron_expression, now)
                schedule.next_run_at = iter_cron.get_next(timezone.datetime)
            except Exception:
                # If error, pause it
                schedule.status = ScheduledMessage.Status.PAUSED
        
        schedule.save()
