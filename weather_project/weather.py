import requests
from datetime import datetime, timedelta


class WeatherFetcher:
    def __init__(self, api_key, country_codes):
        self.api_key = api_key
        self.country_codes = country_codes

    def fetch_weather(self, city):
        """
        Fetches weather data from the OpenWeatherMap API.
        """
        if not city:
            raise ValueError("City name cannot be empty.")

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}"

        try:
            response = requests.get(url)

            # Error handling for different HTTP status codes
            if response.status_code == 404:
                raise ValueError(f"City '{city}' not found. Please check the city name.")
            elif response.status_code == 401:
                raise PermissionError("Invalid API key. Please check your API key.")
            elif response.status_code == 500:
                raise ConnectionError("Server error. Please try again later.")
            elif response.status_code == 429:
                raise RuntimeError("Too many requests. Please wait a moment before trying again.")
            elif response.status_code != 200:
                raise RuntimeError(f"Unexpected error: {response.status_code}")

            data = response.json()
            weather_id = data["weather"][0]["id"]
            icon_code = data["weather"][0]["icon"]
            timezone_offset = data["timezone"]
            temperature_kelvin = data["main"]["temp"]
            feels_like_kelvin = data["main"]["feels_like"]
            temp_min_kelvin = data["main"]["temp_min"]
            temp_max_kelvin = data["main"]["temp_max"]
            temperature_celsius = temperature_kelvin - 273.15
            feels_like_celsius = feels_like_kelvin - 273.15
            temp_min_celsius = temp_min_kelvin - 273.15
            temp_max_celsius = temp_max_kelvin - 273.15

            weather = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            rain_volume = data.get("rain", {}).get("1h", "N/A")
            country_code = data["sys"]["country"]
            country = self.country_codes.get(country_code, "Unknown")
            sunrise_time = self.convert_unix_to_local_time(data["sys"]["sunrise"], timezone_offset)
            sunset_time = self.convert_unix_to_local_time(data["sys"]["sunset"], timezone_offset)

            return {
                "weather_id": weather_id,
                "weather": weather,
                "icon": icon_code,
                "temperature_celsius": temperature_celsius,
                "feels_like_celsius": feels_like_celsius,
                "temp_min_celsius": temp_min_celsius,
                "temp_max_celsius": temp_max_celsius,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "rain_volume": rain_volume,
                "country": country,
                "sunrise_time": sunrise_time,
                "sunset_time": sunset_time
            }
        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            raise RuntimeError(f"Request error occurred: {req_err}")
        except KeyError as key_err:
            raise RuntimeError(f"Missing data in response: {key_err}")
        except Exception as e:
            raise RuntimeError(f"Unable to fetch weather data: {e}")

    def convert_unix_to_local_time(self, unix_timestamp, timezone_offset):
        """
        Converts the time of the sunrise and sunset to the local time.
        """
        utc_time = datetime.utcfromtimestamp(unix_timestamp)
        local_time = utc_time + timedelta(seconds=timezone_offset)
        return local_time.strftime('%H:%M')
