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
from datetime import date
from math import ceil
import os
import smtplib
from email.message import EmailMessage

from config import *

# ==================================================
# PRE-WEATHER MOWING HEIGHT ESTIMATE
# ==================================================

today_date = date.today()

try:
    mowing_history_df = pd.read_csv(MOWING_HISTORY_FILE)
    mowing_history_df["date"] = pd.to_datetime(mowing_history_df["date"])

    last_mow_date = (
        mowing_history_df["date"]
        .max()
        .date()
    )

except Exception as e:
    last_mow_date = None
    print(f"\nCould not read mowing history: {e}")

if last_mow_date is None:
    days_since_last_mow = None
    estimated_grass_height = None
    days_until_preferred_mow = None
    days_until_too_tall = None
    preferred_mow_date = None
    too_tall_date = None
    mowing_forecast_days_needed = 0

else:
    days_since_last_mow = (
        today_date - last_mow_date
    ).days

    estimated_grass_height = (
        POST_MOW_HEIGHT
        + days_since_last_mow * DEFAULT_GRASS_GROWTH_RATE
    )

    days_until_preferred_mow = max(
        0,
        ceil(
            (PREFERRED_MOW_HEIGHT - estimated_grass_height)
            / DEFAULT_GRASS_GROWTH_RATE
        )
    )

    days_until_too_tall = max(
        0,
        ceil(
            (MAX_RECOMMENDED_HEIGHT - estimated_grass_height)
            / DEFAULT_GRASS_GROWTH_RATE
        )
    )

    preferred_mow_date = today_date + pd.Timedelta(
        days=days_until_preferred_mow
    )

    too_tall_date = today_date + pd.Timedelta(
        days=days_until_too_tall
    )

    mowing_forecast_days_needed = max(
        MOWING_PRIMARY_WINDOW_DAYS,
        days_until_too_tall + 1
    )

forecast_days_needed = min(
    MAX_FORECAST_DAYS,
    max(
        FORECAST_DAYS,
        mowing_forecast_days_needed
    )
)

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
    f"&forecast_days={forecast_days_needed}"
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

watering_forecast_start = RECENT_RAIN_DAYS
watering_forecast_end = RECENT_RAIN_DAYS + FORECAST_DAYS

mowing_forecast_start = RECENT_RAIN_DAYS
mowing_forecast_end = RECENT_RAIN_DAYS + forecast_days_needed

forecast_rain = sum(rainfall[watering_forecast_start:watering_forecast_end])
mowing_forecast_rain = rainfall[mowing_forecast_start:mowing_forecast_end]
mowing_forecast_dates = dates[mowing_forecast_start:mowing_forecast_end]

# ==================================================
# READ WATERING CONFIRMATIONS
# ==================================================

try:
    confirmations_df = pd.read_csv(WATERING_CONFIRMATION_CSV_URL)

    confirmations_df.columns = [
        col.strip().lower().replace(" ", "_")
        for col in confirmations_df.columns
    ]

    timestamp_col = confirmations_df.columns[0]

    confirmations_df[timestamp_col] = pd.to_datetime(
        confirmations_df[timestamp_col]
    )

    cutoff_date = pd.Timestamp.today().normalize() - pd.Timedelta(
        days=RECENT_RAIN_DAYS
    )

    recent_confirmations_df = confirmations_df[
        confirmations_df[timestamp_col] >= cutoff_date
    ]

    confirmed_watering_count = (
        recent_confirmations_df[timestamp_col]
        .dt.date
        .nunique()
    )

except Exception as e:
    confirmed_watering_count = 0
    print(f"\nCould not read watering confirmations: {e}")

confirmed_watering_credit = confirmed_watering_count * BASE_WEEKLY_TARGET

weather_stress_end = RECENT_RAIN_DAYS + FORECAST_DAYS

avg_high_temp = (
    sum(high_temps[:weather_stress_end])
    / len(high_temps[:weather_stress_end])
)

avg_dew_point = (
    sum(dew_points[:weather_stress_end])
    / len(dew_points[:weather_stress_end])
)

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
    - confirmed_watering_credit
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
print(f"Confirmed watering credit: {round(confirmed_watering_credit, 2)} inches")

print(
    f"Forecast rain credit: "
    f"{round(effective_forecast_rain, 2)} inches"
)

print(
    f"Estimated water deficit: "
    f"{round(water_deficit, 2)} inches"
)

print(f"\nRecommendation: {recommendation}")

# ==================================================
# MOWING WEATHER WINDOW LOGIC
# ==================================================

primary_good_mowing_dates = []
primary_poor_mowing_dates = []
extended_good_mowing_dates = []
extended_poor_mowing_dates = []

if last_mow_date is None:
    mowing_recommendation = "mowing history unavailable"
    mowing_needed = False
    primary_window_start_date = None
    primary_window_end_date = None
    mowing_planning_end_date = None

else:
    primary_window_start_date = max(
        today_date,
        preferred_mow_date - pd.Timedelta(days=MOWING_EMAIL_WINDOW_DAYS)
    )

    primary_window_end_date = primary_window_start_date + pd.Timedelta(
        days=MOWING_PRIMARY_WINDOW_DAYS - 1
    )

    mowing_planning_end_date = max(
        primary_window_end_date,
        too_tall_date
    )

    recent_heavy_rain = (
        sum(rainfall[
            RECENT_RAIN_DAYS - RECENT_HEAVY_RAIN_LOOKBACK_DAYS:
            RECENT_RAIN_DAYS
        ])
        >= RECENT_HEAVY_RAIN_BLOCKING_INCHES
    )

    for forecast_date, forecast_day_rain in zip(
        mowing_forecast_dates,
        mowing_forecast_rain
    ):
        forecast_date_obj = pd.to_datetime(forecast_date).date()

        if forecast_date_obj < primary_window_start_date:
            continue

        if forecast_date_obj > mowing_planning_end_date:
            continue

        rain_blocks_mowing = (
            forecast_day_rain >= MOWING_BLOCKING_RAIN_INCHES
        )

        recent_rain_blocks_today = (
            forecast_date_obj == today_date
            and recent_heavy_rain
        )

        if rain_blocks_mowing:
            date_note = (
                f"{forecast_date_obj} - rain expected "
                f"({round(forecast_day_rain, 2)} inches)"
            )

            if primary_window_start_date <= forecast_date_obj <= primary_window_end_date:
                primary_poor_mowing_dates.append(date_note)
            else:
                extended_poor_mowing_dates.append(date_note)

        elif recent_rain_blocks_today:
            date_note = (
                f"{forecast_date_obj} - ground may still be wet "
                f"from recent heavy rain"
            )

            if primary_window_start_date <= forecast_date_obj <= primary_window_end_date:
                primary_poor_mowing_dates.append(date_note)
            else:
                extended_poor_mowing_dates.append(date_note)

        else:
            if primary_window_start_date <= forecast_date_obj <= primary_window_end_date:
                primary_good_mowing_dates.append(forecast_date_obj)
            else:
                extended_good_mowing_dates.append(forecast_date_obj)

    if days_until_preferred_mow > MOWING_EMAIL_WINDOW_DAYS:
        mowing_recommendation = "doesn't need mowing"
        mowing_needed = False

    elif days_until_too_tall == 0:
        mowing_recommendation = (
            "mow as soon as possible; grass is likely beyond the "
            "preferred maximum height"
        )
        mowing_needed = True

    elif len(primary_good_mowing_dates) > 0:
        mowing_recommendation = (
            "mowing window is opening; choose a favorable day soon"
        )
        mowing_needed = True

    else:
        mowing_recommendation = (
            "mowing window is opening, but nearby weather looks poor"
        )
        mowing_needed = True
        
# ==================================================
# OUTPUT MOWING RECOMMENDATION
# ==================================================

print("\n==============================")
print("LAWN MOWING RECOMMENDATION")
print("==============================")

print(f"Last mow date: {last_mow_date}")
print(f"Days since last mow: {days_since_last_mow}")
print(f"Post-mow height: {POST_MOW_HEIGHT} inches")
print(f"Max recommended height: {round(MAX_RECOMMENDED_HEIGHT, 2)} inches")
print(f"Preferred mow height: {PREFERRED_MOW_HEIGHT} inches")

print(
    f"Estimated current height: "
    f"{round(estimated_grass_height, 2) if estimated_grass_height is not None else None} inches"
)

print(f"Estimated days until preferred mow: {days_until_preferred_mow}")
print(f"Estimated days until too tall: {days_until_too_tall}")
print(f"Preferred mow date: {preferred_mow_date}")
print(f"Too-tall date: {too_tall_date}")
print(f"Primary mowing window start date: {primary_window_start_date}")
print(f"Primary mowing window end date: {primary_window_end_date}")
print(f"Mowing planning end date: {mowing_planning_end_date}")
print(f"Primary good mowing dates: {primary_good_mowing_dates}")
print(f"Primary poor mowing dates: {primary_poor_mowing_dates}")
print(f"Extended good mowing dates: {extended_good_mowing_dates}")
print(f"Extended poor mowing dates: {extended_poor_mowing_dates}")
print(f"\nMowing recommendation: {mowing_recommendation}")

# ==================================================
# LOG DAILY RESULT
# ==================================================

log_file = "data/watering_history.csv"

today = date.today().isoformat()

new_row = pd.DataFrame([{
    "date": today,
    "recent_rain": round(recent_rain, 3),
    "forecast_rain": round(forecast_rain, 3),
    "forecast_rain_credit": round(effective_forecast_rain, 3),
    "confirmed_watering_credit": round(confirmed_watering_credit, 3),
    "base_target": BASE_WEEKLY_TARGET,
    "adjusted_target": adjusted_target,
    "target_reason": target_reason,
    "avg_high_temp": round(avg_high_temp, 1),
    "avg_dew_point": round(avg_dew_point, 1),
    "water_deficit": round(water_deficit, 3),
    "recommendation": recommendation
}])

if os.path.exists(log_file):
    history_df = pd.read_csv(log_file)

    history_df = history_df[
        history_df["date"] != today
    ]

    history_df = pd.concat(
        [history_df, new_row],
        ignore_index=True
    )

else:
    history_df = new_row

history_df.to_csv(log_file, index=False)

print("\nResult logged to data/watering_history.csv")

# ==================================================
# CONDITIONAL EMAIL NOTIFICATION
# ==================================================

watering_needed = recommendation in EMAIL_RECOMMENDATIONS

if watering_needed or mowing_needed:
    email_address = os.environ.get("EMAIL_ADDRESS")
    email_password = os.environ.get("EMAIL_PASSWORD")

    if email_address is None or email_password is None:
        print("\nEmail not sent: EMAIL_ADDRESS or EMAIL_PASSWORD is missing.")

    else:
        if watering_needed and mowing_needed:
            subject = "Lawn watering and mowing reminder"
        elif watering_needed:
            subject = "Lawn watering reminder"
        else:
            subject = "Lawn mowing reminder"

        body = f"""
WATERING
Recommendation: {recommendation.upper()}

Recent rain, last {RECENT_RAIN_DAYS} days: {round(recent_rain, 2)} inches
Confirmed watering, last {RECENT_RAIN_DAYS} days: {round(confirmed_watering_credit, 2)} inches

Forecast rain, next {FORECAST_DAYS} days: {round(forecast_rain, 2)} inches
Forecast rain credit: {round(effective_forecast_rain, 2)} inches

Base weekly target: {BASE_WEEKLY_TARGET} inches
Adjusted weekly target: {adjusted_target} inches
Target reason: {target_reason}

Estimated water deficit: {round(water_deficit, 2)} inches

After watering, mark it here:
{WATERING_CONFIRMATION_LINK}


MOWING
Recommendation: {mowing_recommendation.upper()}

Last mow date: {last_mow_date}
Days since last mow: {days_since_last_mow}

Post-mow height: {POST_MOW_HEIGHT} inches
Preferred mow height: {PREFERRED_MOW_HEIGHT} inches
Max recommended height: {round(MAX_RECOMMENDED_HEIGHT, 2)} inches
Estimated current height: {round(estimated_grass_height, 2) if estimated_grass_height is not None else None} inches

Estimated days until preferred mow: {days_until_preferred_mow}
Estimated days until too tall: {days_until_too_tall}

Preferred mow date: {preferred_mow_date}
Too-tall date: {too_tall_date}
Firm planning window: {primary_window_start_date} through {primary_window_end_date}
Extended planning window through: {mowing_planning_end_date}

Good mowing dates in firm window:
{primary_good_mowing_dates}

Poor mowing dates in firm window:
{primary_poor_mowing_dates}

Good mowing dates in extended window:
{extended_good_mowing_dates}

Poor mowing dates in extended window:
{extended_poor_mowing_dates}

- Lawn Mailbot
"""

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"Lawn Mailbot <{email_address}>"
        recipient = os.environ.get("EMAIL_RECIPIENT")

        msg["To"] = recipient
        msg["Reply-To"] = email_address
        msg.set_content(body.strip())

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)

        print("\nEmail notification sent.")

else:
    print("\nEmail not sent: no watering or mowing action needed.")