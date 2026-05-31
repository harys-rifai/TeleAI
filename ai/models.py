from django.db import models
from django.conf import settings

class AIConfig(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_config'
    )
    api_key = models.CharField(max_length=150, blank=True, null=True, help_text="Override system OPENAI_API_KEY")
    api_base_url = models.CharField(max_length=250, blank=True, null=True, help_text="Override OpenAI API base URL (e.g., for 9router)")
    model_name = models.CharField(max_length=50, default="gpt-4o")
    system_prompt = models.TextField(default="You are a helpful assistant responding to Telegram inquiries.")
    temperature = models.FloatField(default=0.7)
    is_auto_reply_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_config'

    def __str__(self):
        return f"AI Config for {self.user.email}"
