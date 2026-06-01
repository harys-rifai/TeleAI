from django.db import models
from django.conf import settings

class TelegramAccount(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_accounts'
    )
    api_id = models.IntegerField()
    api_hash = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    bot_token = models.CharField(max_length=100, blank=True, null=True)
    session_string = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'telegram_account'
        unique_together = ('user', 'phone_number')

    def __str__(self):
        return f"{self.phone_number} (User: {self.user.email})"
