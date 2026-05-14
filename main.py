# ==================================================
# Project: lawn_needs_watering
# Description:
# Determine whether lawn watering is needed
# based on recent rainfall and weather forecasts.
#
# Author: David Ford
# ==================================================

# ==================================================
# IMPORTS
# ==================================================

import requests
import pandas as pd

from config import *

# ==================================================
# API REQUEST
# ==================================================

url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LATITUDE}"
    f"&longitude={LONGITUDE}"
    f"&daily=precipitation_sum,"
    f"temperature_2m_max,"
    f"dew_point_2m_mean"
    f"&temperature_unit=fahrenheit"
    f"&precipitation_unit=inch"
    f"&timezone=auto"
    f"&past_days=7"
    f"&forecast_days=3"
)

response = requests.get(url)

data = response.json()

# ==================================================
# EXTRACT DAILY DATA
# ==================================================

dates = data["daily"]["time"]

rainfall = data["daily"]["precipitation_sum"]

high_temps = data["daily"]["temperature_2m_max"]

dew_points = data["daily"]["dew_point_2m_mean"]

# ==================================================
# CREATE DATAFRAME
# ==================================================

weather_df = pd.DataFrame({
    "date": dates,
    "rainfall_inches": rainfall,
    "high_temp_f": high_temps,
    "dew_point_f": dew_points
})

# ==================================================
# OUTPUT
# ==================================================

print("\nWeather Data:\n")

print(weather_df)

recent_rain = sum(rainfall[:RECENT_RAIN_DAYS])
forecast_rain = sum(rainfall[RECENT_RAIN_DAYS:])

print("\nRecent rainfall total:")
print(round(recent_rain, 2), "inches")

print("\nForecast rainfall total:")
print(round(forecast_rain, 2), "inches")

# ==================================================
# WATERING DECISION LOGIC
# ==================================================

effective_forecast_rain = (
    forecast_rain * FORECAST_DISCOUNT
)

water_deficit = (
    BASE_WEEKLY_TARGET
    - recent_rain
    - effective_forecast_rain
)

# ==================================================
# RECOMMENDATION
# ==================================================

if water_deficit <= 0:
    recommendation = "doesn't need watering"

elif water_deficit < 0.30:
    recommendation = "needs light watering"

elif water_deficit < 0.70:
    recommendation = "needs watering"

else:
    recommendation = "needs heavy watering"

# ==================================================
# OUTPUT RECOMMENDATION
# ==================================================

print("\n==============================")
print("LAWN WATERING RECOMMENDATION")
print("==============================")

print(f"Weekly target: {BASE_WEEKLY_TARGET} inches")
print(f"Recent rain credit: {round(recent_rain, 2)} inches")

print(
    f"Forecast rain credit: "
    f"{round(effective_forecast_rain, 2)} inches"
)

print(
    f"Estimated water deficit: "
    f"{round(water_deficit, 2)} inches"
)

print(f"\nRecommendation: {recommendation}")