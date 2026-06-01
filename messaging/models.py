from django.db import models
from django.conf import settings
from telegram.models import TelegramAccount

class MessageLog(models.Model):
    class Direction(models.TextChoices):
        INBOUND = 'inbound', 'Inbound'
        OUTBOUND = 'outbound', 'Outbound'

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        PENDING = 'pending', 'Pending'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_logs'
    )
    telegram_account = models.ForeignKey(
        TelegramAccount,
        on_delete=models.CASCADE,
        related_name='message_logs'
    )
    chat_id = models.CharField(max_length=100)
    chat_title = models.CharField(max_length=200, blank=True, null=True)
    message_text = models.TextField()
    direction = models.CharField(
        max_length=10,
        choices=Direction.choices,
        default=Direction.OUTBOUND
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SUCCESS
    )

    class Meta:
        db_table = 'message_log'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.direction.upper()} to {self.chat_id} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
