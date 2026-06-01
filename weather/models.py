from django.db import models
from django.conf import settings

class WeatherLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weather_locations'
    )
    location_name = models.CharField(max_length=100)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    target_chat_id = models.CharField(max_length=150)
    schedule_time = models.TimeField(default="08:00")
    last_run_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'weather_location'
        ordering = ['schedule_time']

    def __str__(self):
        return f"Weather for {self.location_name} (Send to {self.target_chat_id})"
