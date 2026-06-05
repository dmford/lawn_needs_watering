# lawn_needs_watering

A Python home-automation project that monitors lawn watering and mowing needs using recent weather, forecast weather, Google Sheets logs, and daily GitHub Actions automation.

The script sends an email only when action is recommended: watering, mowing, or both.

## What It Does

Each run:

1. Pulls recent and forecast weather data from Open-Meteo.
2. Calculates recent rainfall and discounted forecast rainfall.
3. Adjusts watering recommendations based on temperature and humidity.
4. Reads confirmed watering history from Google Sheets.
5. Reads mowing history from Google Sheets.
6. Estimates current grass height from the last recorded mow.
7. Identifies good and poor mowing dates based on forecast rain.
8. Sends a concise email only when watering or mowing is recommended.
9. Includes embedded links for recording watering and mowing events.

## Current Model

### Watering

The baseline weekly target is 1.25 inches of water.

The approximate water deficit is:

```text
water_deficit =
    adjusted_weekly_target
  - recent_rain
  - confirmed_watering_credit
  - discounted_forecast_rain
```

Confirmed watering is read from a Google Sheet populated by a one-click Apps Script link.

### Mowing

Mowing recommendations are based on:

* last recorded mow date
* post-mow height
* estimated daily grass growth rate
* preferred mowing height
* maximum preferred height
* near-term forecast rain

Mowing records are submitted through a Google Apps Script form and stored in a separate Google Sheet. The form records mowing date, pre-mow height measurements, ground condition, cut quality, clipping handling, clipping result, reason, and optional notes.

## Automation

The GitHub Actions workflow runs daily at approximately:

```text
8:30 AM Eastern during daylight saving time
```

The workflow can also be run manually from the GitHub Actions tab.

## Email Notifications

Emails are sent only when action is recommended.

Subject lines are:

```text
[Lawn] Water + Mow
[Lawn] Watering Required
[Lawn] Mowing Window Open
```

The email is designed for quick mobile reading:

1. Actionable recommendation first.
2. Embedded logging links near the top.
3. Supporting details lower in the email.

## Private Configuration

Email credentials are not stored in the repository.

The GitHub Actions workflow expects these repository secrets:

```text
EMAIL_ADDRESS
EMAIL_PASSWORD
EMAIL_RECIPIENT
```

## Files

```text
main.py                         Main script
config.py                       Configuration values, thresholds, and public logging URLs
requirements.txt                Python dependencies
data/watering_history.csv        Local recommendation history
data/mowing_history.csv          Local fallback/seed mowing history
.github/workflows/daily_run.yml  GitHub Actions schedule
```

## Future Improvements

Possible later improvements:

* DST-proof scheduling
* seasonal watering adjustments
* more liberal new-lawn watering settings
* sprinkler runtime calibration
* learned grass-growth model from mowing records
* evapotranspiration modeling
* improved dashboard or visualization
* duplicate-notification suppression
* richer mowing recommendation wording after real-world usage

## Author

David Ford

This project was developed by David Ford with AI-assisted coding support from ChatGPT for debugging, documentation, workflow planning, implementation support, and code review. Project design, implementation decisions, validation, interpretation, and final repository contents were reviewed and approved by the author.
