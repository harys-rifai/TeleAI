from django.db import models
from django.conf import settings
from django.utils import timezone
from telegram.models import TelegramAccount

class ScheduledMessage(models.Model):
    class ScheduleType(models.TextChoices):
        ONCE = 'once', 'Once'
        INTERVAL = 'interval', 'Interval'
        CRON = 'cron', 'Cron'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        COMPLETED = 'completed', 'Completed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_messages'
    )
    telegram_account = models.ForeignKey(
        TelegramAccount,
        on_delete=models.CASCADE,
        related_name='scheduled_messages'
    )
    target_chat_id = models.CharField(max_length=150)
    message_text = models.TextField()
    schedule_type = models.CharField(
        max_length=10,
        choices=ScheduleType.choices,
        default=ScheduleType.ONCE
    )
    interval_seconds = models.IntegerField(default=60, help_text="Used if schedule_type is 'interval'")
    cron_expression = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Standard crontab format, e.g. '*/5 * * * *'"
    )
    last_run_at = models.DateTimeField(blank=True, null=True)
    next_run_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scheduled_message'
        ordering = ['next_run_at']

    def __str__(self):
        return f"Schedule for {self.target_chat_id} ({self.get_schedule_type_display()})"
