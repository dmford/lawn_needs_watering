# Lawn Watering and Mowing Automation

A Python-based home automation project that uses weather data, historical maintenance records, and scheduled cloud workflows to automate lawn-care recommendations.

The system evaluates watering and mowing needs each day using recent weather, forecast weather, and user-maintained activity logs. Recommendations are delivered by email only when action is likely to be beneficial.

The project serves as an example of practical automation, decision-support systems, API integration, and cloud-based scheduling.

## Project Goal

The objective is to automate routine lawn-care decisions using weather data and historical observations.

Rather than manually checking forecasts, estimating rainfall deficits, and tracking mowing intervals, the system evaluates conditions automatically and generates actionable recommendations when intervention is warranted.

The long-term goal is to evolve the system from a rule-based recommendation engine into a data-driven forecasting tool that learns grass-growth behavior from accumulated mowing records.

## What It Does

Each daily run:

1. Pulls recent and forecast weather data from Open-Meteo.
2. Calculates recent rainfall and discounted forecast rainfall.
3. Adjusts watering recommendations based on temperature and humidity.
4. Reads confirmed watering history from Google Sheets.
5. Reads mowing history from Google Sheets.
6. Estimates current grass height from the last recorded mow.
7. Identifies favorable and unfavorable mowing windows based on forecast conditions.
8. Generates watering and mowing recommendations.
9. Sends an email only when action is recommended.
10. Includes embedded links for recording watering and mowing events.

## Decision Models

### Watering

The baseline weekly target is 1.25 inches of water.

The approximate water deficit is calculated as:

```text
water_deficit =
    adjusted_weekly_target
  - recent_rain
  - confirmed_watering_credit
  - discounted_forecast_rain
```

Confirmed watering events are recorded through a Google Apps Script logging link and stored in Google Sheets.

The model adjusts recommendations based on:

* Recent rainfall
* Forecast rainfall
* Temperature conditions
* Humidity conditions
* Confirmed watering history

### Mowing

Mowing recommendations are based on:

* Last recorded mow date
* Post-mow height
* Estimated daily growth rate
* Preferred mowing height
* Maximum preferred height
* Near-term forecast weather

Mowing records are submitted through a Google Apps Script form and stored in Google Sheets.

Recorded information includes:

* Mowing date
* Pre-mow height measurements
* Ground condition
* Cut quality
* Clipping handling
* Clipping results
* Reason for mowing
* Optional notes

## Automation

The system runs automatically through GitHub Actions.

Scheduled execution occurs daily at approximately:

```text
8:30 AM Eastern during daylight saving time
```

The workflow may also be executed manually from the GitHub Actions interface.

## Email Notifications

Emails are sent only when action is recommended.

Possible subject lines include:

```text
[Lawn] Water + Mow
[Lawn] Watering Required
[Lawn] Mowing Window Open
```

The email format is optimized for quick mobile review:

1. Recommended action first.
2. Embedded logging links near the top.
3. Supporting details below.
4. Weather and scheduling context when relevant.

## Technologies Used

* Python
* GitHub Actions
* Open-Meteo API
* Google Sheets
* Google Apps Script
* SMTP Email Automation

## Repository Structure

```text
main.py                          Main application logic
config.py                        Configuration values and thresholds
requirements.txt                 Python dependencies

data/
    watering_history.csv         Local watering history
    mowing_history.csv           Local mowing history

.github/workflows/
    daily_run.yml                Scheduled GitHub Actions workflow
```

## Private Configuration

Email credentials and other sensitive information are not stored in the repository.

The GitHub Actions workflow expects the following repository secrets:

```text
EMAIL_ADDRESS
EMAIL_PASSWORD
EMAIL_RECIPIENT
```

## Future Improvements

Potential future extensions include:

* Data-driven grass-growth forecasting using accumulated mowing observations
* Weather-history storage for model training and validation
* Seasonal growth-rate estimation
* Evapotranspiration-based watering recommendations
* Improved dashboard and visualization tools
* Enhanced notification logic
* More sophisticated mowing-window forecasting
* Long-term model calibration using observed lawn outcomes

## Author

David Ford

This project was developed by David Ford with AI-assisted coding support from ChatGPT for debugging, documentation, workflow planning, implementation support, and code review. Project design, implementation decisions, validation, interpretation, and final repository contents were reviewed and approved by the author.
