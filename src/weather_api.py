# File: src/export_data.py
# Description: Handles all exporting of tasks and schedules.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-23

# Imports.
import asyncio
from datetime import datetime, date as date_cls
import python_weather # Requires: python-weather==2.1.0

# Gets the weather for a location and date from weather API.
async def get_weather(location: str, date: str):
    # Gets the date to the correct format.
    try:
        target_date: date_cls = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    try:
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
            forecast = await client.get(location)
            # Checks daily forecast first.
            for daily in forecast.daily_forecasts:
                if daily.date == target_date:
                    return (
                        f"Weather for {location} on {date}: "
                        f"Condition: {forecast.description}, "
                        f"Temperature: {daily.temperature} °F, "
                        f"High: {daily.highest_temperature} °F, "
                        f"Low: {daily.lowest_temperature} °F.\n"
                    )

            # Backup if daily fails.
            if forecast.datetime.date() == target_date:
                return (
                    f"Weather for {location} on {target_date}: "
                    f"Condition: {forecast.description}, "
                    f"Temperature: {forecast.temperature} °F.\n"
                )
            # API only reaches a week out so check if in range.
            return {
                "error": (
                    "Date not available in forecast range. "
                )
            }

    # All encompassing exception if the API can't be reached or times out.
    except Exception as e:
        return {"Weather at this location and date could not be reached"}

#Sync function so it can be called.
def get_weather_sync(location: str, date: str):
    return asyncio.run(get_weather(location, date))
