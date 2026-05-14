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

avg_high_temp = sum(high_temps) / len(high_temps)
avg_dew_point = sum(dew_points) / len(dew_points)

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

if (
    avg_high_temp >= HOT_TEMP_THRESHOLD
    and avg_dew_point < VERY_DRY_DEW_POINT_THRESHOLD
):
    adjusted_target = HOT_DRY_TARGET
    target_reason = "hot and dry conditions"

elif (
    avg_high_temp <= COOL_TEMP_THRESHOLD
    and avg_dew_point >= HUMID_DEW_POINT_THRESHOLD
):
    adjusted_target = COOL_HUMID_TARGET
    target_reason = "cool and humid conditions"

else:
    adjusted_target = BASE_WEEKLY_TARGET
    target_reason = "normal conditions"

water_deficit = (
    adjusted_target
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

print(f"Base weekly target: {BASE_WEEKLY_TARGET} inches")
print(f"Adjusted weekly target: {adjusted_target} inches")
print(f"Target reason: {target_reason}")
print(f"Average high temp: {round(avg_high_temp, 1)} F")
print(f"Average dew point: {round(avg_dew_point, 1)} F")
print(f"Recent rain credit: {round(recent_rain, 2)} inches")
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