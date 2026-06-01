import requests
from django.conf import settings

def resolve_coordinates(location_name):
    """Geocode location using free Open-Meteo Geocoding API."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(location_name)}&count=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = data.get('results', [])
            if results:
                loc = results[0]
                return loc.get('latitude'), loc.get('longitude'), loc.get('name')
    except Exception as e:
        # Silently fail for geocoding but log it
        print(f"[Geocoding Error] {e}")
    return None, None, location_name

def map_weather_code(code):
    """Map Open-Meteo WMO codes to human readable strings."""
    codes = {
        0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
        45: "Foggy 🌫️", 48: "Depositing rime fog 🌫️",
        51: "Light drizzle 🌧️", 53: "Moderate drizzle 🌧️", 55: "Dense drizzle 🌧️",
        61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
        71: "Slight snow fall ❄️", 73: "Moderate snow fall ❄️", 75: "Heavy snow fall ❄️",
        80: "Slight rain showers 🌦️", 81: "Moderate rain showers 🌦️", 82: "Violent rain showers 🌦️",
        95: "Thunderstorm ⛈️"
    }
    return codes.get(code, "Cloudy ☁️")

def fetch_weather_report(lat, lon, location_name):
    """Fetch weather report string for Telegram messages."""
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', None) or getattr(settings, 'WEATHER_API_KEY', None)
    if api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                d = res.json()
                return f"☀️ Weather Report for {location_name}:\n- Temp: {d['main']['temp']}°C\n- Status: {d['weather'][0]['description'].capitalize()}\n- Humidity: {d['main']['humidity']}%"
        except Exception: pass

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            cw = data.get('current_weather', {})
            return f"☀️ Weather Report for {location_name}:\n- Temp: {cw.get('temperature')}°C\n- Status: {map_weather_code(cw.get('weathercode'))}\n- Wind: {cw.get('windspeed')} km/h"
    except Exception as e:
        print(f"[Weather Fetch Error] {e}")
    return f"⚠️ Weather Alert: Could not fetch updates for {location_name} at this time."