from datetime import date
import requests
import os
import json
from . import date_utils
from typing import TypedDict

class WeatherRequest(TypedDict):
    location: str
    city: str

class ForeCastResponse(TypedDict):
    time: str
    temperature: str
    condition: str
    windSpeed: str
    humidity: str
    precipitationProbability: str

def parse_json(json_string: str) -> dict:
    return json.loads(json_string)

def classify_temperature(temp: float) -> str:
    if temp < 0:
        return "Freezing"
    elif 0 <= temp < 10:
        return "Cold"
    elif 10 <= temp < 20:
        return "Cool"
    elif 20 <= temp < 30:
        return "Warm"
    else:
        return "Hot"

def get_condition(code: int) -> str:
    conditions = {
        0: "Unknown",
        1000: "Clear, Sunny",
        1100: "Mostly Clear",
        1101: "Partly Cloudy",
        1102: "Mostly Cloudy",
        1001: "Cloudy",
        2000: "Fog",
        2100: "Light Fog",
        4000: "Drizzle",
        4001: "Rain",
        4200: "Light Rain",
        4201: "Heavy Rain",
        5000: "Snow",
        5001: "Flurries",
        5100: "Light Snow",
        5101: "Heavy Snow",
        6000: "Freezing Drizzle",
        6001: "Freezing Rain",
        6200: "Light Freezing Rain",
        6201: "Heavy Freezing Rain",
        7000: "Ice Pellets",
        7101: "Heavy Ice Pellets",
        7102: "Light Ice Pellets",
        8000: "Thunderstorm"
    }
    return conditions.get(code, "Unknown")

def get_weather(location: str) -> dict:
    api_key = os.getenv("TOMORROW_API_KEY")
    
    if not api_key:
        raise ValueError("TOMORROW_API_KEY environment variable not set")

    response = requests.get(f"https://api.tomorrow.io/v4/weather/realtime?location={location}&apikey={api_key}")

    if response.status_code == 200:
        data = parse_json(response.text)
        temperature = data['data']['values']['temperature']
        
        return {
            "location": location,
            "classification": classify_temperature(temperature),
            "temperature": f"{temperature}°C",
            "condition": get_condition(data['data']['values']['weatherCode'])
        }
    else:
        raise Exception("Failed to fetch weather data")
    
def transform_forecast_data(data: dict) -> ForeCastResponse:
    values = data.get('values', {})
    condition = get_condition(values.get('weatherCode', 0))
    
    return {
        "time": data.get('time', ''),
        "temperature": f"{values.get('temperature', 0)}°C",
        "condition": condition,
        "windSpeed": f"{values.get('windSpeed', 0)} km/h",
        "precipitationProbability": f"{values.get('precipitationProbability', 0)}",
        "humidity": f"{values.get('humidity', 0)}%"
    }

def filter_forecast_by_date(forecasts: list[ForeCastResponse], target_date: str) -> list[ForeCastResponse]:
    return [forecast for forecast in forecasts if forecast['time'].startswith(target_date)]

def summarize_forecast(forecasts: list[ForeCastResponse]) -> str:
    if not forecasts:
        return "No forecast data available for the specified date."

    temperatures = []
    conditions = []
    precipitation_probs = []
    
    for forecast in forecasts:
        temp_str = forecast['temperature'].replace('°C', '')
        try:
            temp = float(temp_str)
            temperatures.append(temp)
        except ValueError:
            pass
            
        conditions.append(forecast['condition'].lower())
        
        precip_str = forecast['precipitationProbability']
        try:
            precip = float(precip_str)
            precipitation_probs.append(precip)
        except ValueError:
            pass
    
    summary = []
    
    if temperatures:
        avg_temp = sum(temperatures) / len(temperatures)
        max_temp = max(temperatures)
        min_temp = min(temperatures)
        
        temp_classification = classify_temperature(avg_temp)
        
        if avg_temp < 10:
            summary.append(f"It will be {temp_classification.lower()} with temperatures ranging from {min_temp}°C to {max_temp}°C (average {avg_temp:.1f}°C).")
        elif avg_temp > 25:
            summary.append(f"It will be {temp_classification.lower()} with temperatures ranging from {min_temp}°C to {max_temp}°C (average {avg_temp:.1f}°C).")
        else:
            summary.append(f"It will be {temp_classification.lower()} with temperatures ranging from {min_temp}°C to {max_temp}°C (average {avg_temp:.1f}°C).")
    
    if precipitation_probs:
        max_precip = max(precipitation_probs)
        avg_precip = sum(precipitation_probs) / len(precipitation_probs)
        
        if max_precip > 70:
            summary.append("Yes, it will likely rain with high probability of precipitation.")
        elif max_precip > 40:
            summary.append("There's a moderate chance of rain.")
        elif max_precip > 20:
            summary.append("There's a slight chance of rain.")
        else:
            summary.append("It's unlikely to rain.")
    
    rain_conditions = ['rain', 'drizzle', 'thunderstorm', 'snow']
    will_rain = any(any(rain_word in condition for rain_word in rain_conditions) for condition in conditions)
    
    if will_rain:
        summary.append("Expect wet weather conditions.")
    
    summary.append("\nHourly breakdown:")
    for forecast in forecasts:
        summary.append(f"• {forecast['time']}: {forecast['temperature']} with {forecast['condition']}, {forecast['precipitationProbability']}% chance of rain")

    return "\n".join(summary)

def get_forecast(location: str) -> list[ForeCastResponse]:
    api_key = os.getenv("TOMORROW_API_KEY")
    
    if not api_key:
        raise ValueError("TOMORROW_API_KEY environment variable not set")

    response = requests.get(f"https://api.tomorrow.io/v4/weather/forecast", params={
        "apikey": api_key,
        "location": location,
        "timesteps": ["1h"],
        "units": "metric"
    })

    if response.status_code == 200:
        records = parse_json(response.text)
        
        return list(map(transform_forecast_data, records['timelines']['hourly']))
    else:
        print("Error fetching forecast:", response.text)
        raise Exception("Failed to fetch weather forecast")

def forecast_weather(location: str, period: str) -> str:
    """
    Get a weather forecast for a given location, valid for up to 5 days in 1-hour increments. 
    Provides intelligent analysis answering questions like "will it be hot?", "will it be cold?", "will it rain?".
    
    Use this tool to answer queries such as:
    - "Will it be cold in Paris next tomorrow"
    - "Will it be hot in New York tomorrow?"
    - "Will it rain in London today?"

    Args:
        location (str): The longitude and latitude of the location.
            Example: "48.8566,2.3522" for Paris or "34.0522,-118.2437" for Los Angeles.

        period (str): A string representing a date in this format YYYY-MM-DD
            Supported values include:
                - Keywords:
                    - "today" → current date
                    - "tomorrow" → current date + 1 day
                    - "next tomorrow" or "the day after tomorrow" → current date + 2 days
                - Relative time expressions:
                    - "a day time" → current date + 1 day
                    - "two days time" → current date + 2 days
                    - Up to "five days time" → current date + 5 days
                    
    """
    date = date_utils.normalize_date(period)
    print("Fetching forecast for:", location, "on:", date_utils.normalize_date(period))
    weathers = get_forecast(location)
    filtered = filter_forecast_by_date(weathers, date)
    summary = summarize_forecast(filtered)
    
    return summary

def compare_weather(requests: list[WeatherRequest]) -> str:
    """Compare weather for multiple locations. Compare the weather between two locations. Determines which location is warmer, colder, or if they are the same.

    Args:
        requests (list[WeatherRequest]): A list of dictionaries with keys:
            location: This is the longitude and latitude of the location. For example: "48.8566,2.3522" for Paris or "34.0522,-118.2437" for Los Angeles
            city: This is the name of the city. For example: "Paris" or "Los Angeles"
    """
    results = []
    for req in requests:
        weather = get_weather(req.get('location'))
        results.append(f"The current weather in {req.get('city')} is {weather['classification']} with a temperature of {weather['temperature']} and conditions are {weather['condition']}.")
    
    return "\n".join(results)
    
def fetch_weather(request: WeatherRequest) -> str:
    """Get current weather for a given location

    Args:
        request (WeatherRequest): A dictionary with keys:
            location: This is the longitude and latitude of the location. For example: "48.8566,2.3522" for Paris or "34.0522,-118.2437" for Los Angeles
            city: This is the name of the city. For example: "Paris" or "Los Angeles"
    """
    weather = get_weather(request.get('location'))
    return f"The current weather in {request.get('city')} is {weather['classification']} with a temperature of {weather['temperature']} and conditions are {weather['condition']}."
