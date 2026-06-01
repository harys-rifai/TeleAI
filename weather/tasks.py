import requests
# pyrefly: ignore [missing-import]
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from telegram.models import TelegramAccount
from telegram.telethon_helper import send_message
from messaging.models import MessageLog
from analytics.clickhouse_client import log_message_event
from .models import WeatherLocation

def fetch_weather_report(lat, lon, location_name):
    """
    Fetch weather details using OpenWeather or Open-Meteo API.
    """
    api_key = settings.OPENWEATHER_API_KEY
    if api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                humidity = data['main']['humidity']
                return f"☀️ Weather Report for {location_name}:\n- Temp: {temp}°C\n- Status: {desc.capitalize()}\n- Humidity: {humidity}%"
        except Exception as e:
            print(f"[Weather Task] OpenWeather error: {e}, falling back to Open-Meteo")

    # Fallback to free Open-Meteo (No key required)
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            cw = data.get('current_weather', {})
            temp = cw.get('temperature', 'N/A')
            wind = cw.get('windspeed', 'N/A')
            code = cw.get('weathercode', 0)
            
            # Map weather codes
            weather_descriptions = {
                0: "Clear sky ☀️",
                1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
                45: "Foggy 🌫️", 48: "Depositing rime fog 🌫️",
                51: "Light drizzle 🌧️", 53: "Moderate drizzle 🌧️", 55: "Dense drizzle 🌧️",
                61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
                71: "Slight snow fall ❄️", 73: "Moderate snow fall ❄️", 75: "Heavy snow fall ❄️",
                80: "Slight rain showers 🌦️", 81: "Moderate rain showers 🌦️", 82: "Violent rain showers 🌦️",
                95: "Thunderstorm ⛈️"
            }
            desc = weather_descriptions.get(code, "Cloudy ☁️")
            return f"☀️ Weather Report for {location_name} (via Open-Meteo):\n- Temp: {temp}°C\n- Status: {desc}\n- Wind: {wind} km/h"
    except Exception as e:
        print(f"[Weather Task] Open-Meteo error: {e}")
        
    return f"⚠️ Weather Alert:\nCould not fetch weather updates for {location_name} at this time."

@shared_task
def send_weather_updates():
    """
    Periodic task to send scheduled weather updates.
    """
    now = timezone.now()
    # Convert UTC to local time with SCHEDULER_TZ_OFFSET (e.g., UTC+7 for WITA)
    utc_hour = now.hour
    utc_minute = now.minute
    local_hour = (utc_hour + settings.SCHEDULER_TZ_OFFSET) % 24
    
    # Select active weather tasks scheduled at the current local time
    locations = WeatherLocation.objects.filter(
        is_active=True,
        schedule_time__hour=local_hour,
        schedule_time__minute=utc_minute
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
