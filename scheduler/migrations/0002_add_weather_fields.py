# Generated migration for weather fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledmessage',
            name='latitude',
            field=models.FloatField(blank=True, help_text='Latitude for weather-based messages', null=True),
        ),
        migrations.AddField(
            model_name='scheduledmessage',
            name='longitude',
            field=models.FloatField(blank=True, help_text='Longitude for weather-based messages', null=True),
        ),
        migrations.AddField(
            model_name='scheduledmessage',
            name='location_name',
            field=models.CharField(blank=True, help_text='Location name for weather-based messages', max_length=100, null=True),
        ),
    ]