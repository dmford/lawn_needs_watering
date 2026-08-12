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

today_date = date.today()
WATERING_FORM_BASE_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSdHwtjJ3XwA2mXQXqwbGNDJ3b1QVC0KKtju52HkLG-z_o9daA/"
    "viewform"
)

watering_confirmation_link = (
    f"{WATERING_FORM_BASE_URL}"
    f"?usp=pp_url"
    f"&entry.742209043=Yes"
    f"&entry.1119456750={today_date.isoformat()}"
)

def format_date_list(date_list):
    if len(date_list) == 0:
        return "None"

    return "\n".join(
        f"- {single_date.strftime('%a, %b')} {single_date.day}"
        for single_date in date_list
    )


def format_note_list(note_list):
    if len(note_list) == 0:
        return "None"

    return "\n".join(
        f"- {note}"
        for note in note_list
    )


def format_html_date_list(date_list):
    if len(date_list) == 0:
        return "<p>None</p>"

    items = "".join(
        f"<li>{single_date.strftime('%a, %b')} {single_date.day}</li>"
        for single_date in date_list
    )

    return f"<ul>{items}</ul>"


def format_html_note_list(note_list):
    if len(note_list) == 0:
        return "<p>None</p>"

    items = "".join(
        f"<li>{note}</li>"
        for note in note_list
    )

    return f"<ul>{items}</ul>"


def format_mowing_action(date_list):
    if len(date_list) == 0:
        return "MOW AS SOON AS WEATHER ALLOWS"

    weekday_names = [
        single_date.strftime("%A").upper()
        for single_date in date_list
    ]

    if len(weekday_names) == 1:
        return f"MOW {weekday_names[0]}"

    if len(weekday_names) == 2:
        return f"MOW {weekday_names[0]} OR {weekday_names[1]}"

    return (
        "MOW "
        + ", ".join(weekday_names[:-1])
        + f", OR {weekday_names[-1]}"
    )


def calculate_decayed_watering_credit(watering_dates):
    today_timestamp = pd.Timestamp.today().normalize()

    valid_dates = (
        pd.to_datetime(watering_dates, errors="coerce")
        .dropna()
        .dt.normalize()
        .drop_duplicates()
    )

    total_credit = 0

    for watering_date in valid_dates:
        age_days = (today_timestamp - watering_date).days

        if age_days < 0:
            continue

        if age_days >= RECENT_RAIN_DAYS:
            continue

        age_weight = (RECENT_RAIN_DAYS - age_days) / RECENT_RAIN_DAYS

        total_credit += BASE_WEEKLY_TARGET * age_weight

    return total_credit

# ==================================================
# PRE-WEATHER MOWING HEIGHT ESTIMATE
# ==================================================

active_post_mow_height = POST_MOW_HEIGHT
active_max_recommended_height = MAX_RECOMMENDED_HEIGHT

try:
    try:
        mowing_history_df = pd.read_csv(MOWING_CONFIRMATION_CSV_URL)
        mowing_date_col = "mowing_date"

    except Exception:
        mowing_history_df = pd.read_csv(MOWING_HISTORY_FILE)
        mowing_date_col = "date"

    mowing_history_df.columns = [
        col.strip().lower().replace(" ", "_")
        for col in mowing_history_df.columns
    ]

    mowing_history_df[mowing_date_col] = pd.to_datetime(
        mowing_history_df[mowing_date_col],
        errors="coerce"
    )

    mowing_history_df = mowing_history_df.dropna(
        subset=[mowing_date_col]
    )

    if mowing_history_df.empty:
        raise ValueError("No valid mowing dates found.")

    latest_mow_idx = mowing_history_df[mowing_date_col].idxmax()

    last_mow_date = (
        mowing_history_df.loc[latest_mow_idx, mowing_date_col]
        .date()
    )

    if "post_mow_height" in mowing_history_df.columns:
        latest_post_mow_height = pd.to_numeric(
            pd.Series([
                mowing_history_df.loc[latest_mow_idx, "post_mow_height"]
            ]),
            errors="coerce"
        ).iloc[0]

        if pd.notna(latest_post_mow_height):
            active_post_mow_height = float(latest_post_mow_height)
            active_max_recommended_height = (
                active_post_mow_height * MAX_HEIGHT_MULTIPLIER
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
        active_post_mow_height
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
            (active_max_recommended_height - estimated_grass_height)
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

today_index = RECENT_RAIN_DAYS

recent_rain = sum(rainfall[:today_index + 1])

watering_forecast_start = today_index + 1
watering_forecast_end = watering_forecast_start + FORECAST_DAYS

mowing_forecast_start = today_index
mowing_forecast_end = today_index + forecast_days_needed

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

    if "watering_date" in confirmations_df.columns:
        watering_date_col = "watering_date"

        confirmations_df[watering_date_col] = pd.to_datetime(
            confirmations_df[watering_date_col],
            errors="coerce"
        )

    else:
        watering_date_col = confirmations_df.columns[0]

        confirmations_df[watering_date_col] = pd.to_datetime(
            confirmations_df[watering_date_col],
            errors="coerce"
        )

    confirmations_df = confirmations_df.dropna(
        subset=[watering_date_col]
    )

    confirmed_watering_credit = calculate_decayed_watering_credit(
        confirmations_df[watering_date_col]
    )

except Exception as e:
    confirmed_watering_credit = 0
    print(f"\nCould not read watering confirmations: {e}")

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
print(f"Post-mow height: {active_post_mow_height} inches")
print(f"Max recommended height: {round(active_max_recommended_height, 2)} inches")
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

today = today_date.isoformat()

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
            subject = "[Lawn] Water + Mow"
        elif watering_needed:
            subject = "[Lawn] Watering Required"
        else:
            subject = "[Lawn] Mowing Window Open"

        watering_action_text = ""
        watering_action_html = ""

        if watering_needed:
            watering_action_text = f"""
WATERING REQUIRED

Deficit: {round(water_deficit, 2)}" (target {adjusted_target}")

After watering: {watering_confirmation_link}
"""

            watering_action_html = f"""
<h2>WATERING REQUIRED</h2>
<p>Deficit: {round(water_deficit, 2)}&quot; (target {adjusted_target}&quot;)</p>
<p>After watering: <a href="{watering_confirmation_link}">Record watering</a></p>
"""

        mowing_action_text = ""
        mowing_action_html = ""

        if mowing_needed:
            mowing_action = format_mowing_action(primary_good_mowing_dates)

            mowing_action_text = f"""
{mowing_action}

Height: {round(estimated_grass_height, 2) if estimated_grass_height is not None else None}" (target ≤{round(active_max_recommended_height, 2)}")

After mowing: {MOWING_CONFIRMATION_LINK}
"""

            mowing_action_html = f"""
<h2>{mowing_action}</h2>
<p>Height: {round(estimated_grass_height, 2) if estimated_grass_height is not None else None}&quot; (target ≤{round(active_max_recommended_height, 2)}&quot;)</p>
<p>After mowing: <a href="{MOWING_CONFIRMATION_LINK}">Record mowing</a></p>
"""

        body = f"""
{watering_action_text}

{mowing_action_text}

--------------------

DETAILS

Good mowing dates:
{format_date_list(primary_good_mowing_dates)}

Avoid:
{format_note_list(primary_poor_mowing_dates)}

Extended good mowing dates:
{format_date_list(extended_good_mowing_dates)}

Extended avoid dates:
{format_note_list(extended_poor_mowing_dates)}

Watering:
Recent rain: {round(recent_rain, 2)}"
Forecast rain: {round(forecast_rain, 2)}"
Forecast rain credit: {round(effective_forecast_rain, 2)}"
Water deficit: {round(water_deficit, 2)}"

Mowing:
Last mow date: {last_mow_date}
Estimated height: {round(estimated_grass_height, 2) if estimated_grass_height is not None else None}"
Preferred height: {PREFERRED_MOW_HEIGHT}"
Max preferred height: {round(active_max_recommended_height, 2)}"

Manual logging links:
Watering: {watering_confirmation_link}
Mowing: {MOWING_CONFIRMATION_LINK}

- Lawn Mailbot
"""

        html_body = f"""
<html>
  <body>
    {watering_action_html}

    {mowing_action_html}

    <hr>

    <h3>Details</h3>

    <p><strong>Good mowing dates:</strong></p>
    {format_html_date_list(primary_good_mowing_dates)}

    <p><strong>Avoid:</strong></p>
    {format_html_note_list(primary_poor_mowing_dates)}

    <p><strong>Extended good mowing dates:</strong></p>
    {format_html_date_list(extended_good_mowing_dates)}

    <p><strong>Extended avoid dates:</strong></p>
    {format_html_note_list(extended_poor_mowing_dates)}

    <p><strong>Watering:</strong><br>
    Recent rain: {round(recent_rain, 2)}&quot;<br>
    Forecast rain: {round(forecast_rain, 2)}&quot;<br>
    Forecast rain credit: {round(effective_forecast_rain, 2)}&quot;<br>
    Water deficit: {round(water_deficit, 2)}&quot;</p>

    <p><strong>Mowing:</strong><br>
    Last mow date: {last_mow_date}<br>
    Estimated height: {round(estimated_grass_height, 2) if estimated_grass_height is not None else None}&quot;<br>
    Preferred height: {PREFERRED_MOW_HEIGHT}&quot;<br>
    Max preferred height: {round(active_max_recommended_height, 2)}&quot;</p>

    <p><strong>Manual logging links:</strong><br>
    <a href="{watering_confirmation_link}">Record watering</a><br>
    <a href="{MOWING_CONFIRMATION_LINK}">Record mowing</a></p>

    <p>- Lawn Mailbot</p>
  </body>
</html>
"""

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"Lawn Mailbot <{email_address}>"
        recipient = os.environ.get("EMAIL_RECIPIENT")

        msg["To"] = recipient
        msg["Reply-To"] = email_address
        msg.set_content(body.strip())
        msg.add_alternative(html_body.strip(), subtype="html")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)

        print("\nEmail notification sent.")

else:
    print("\nEmail not sent: no watering or mowing action needed.")