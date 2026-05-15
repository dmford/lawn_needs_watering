# lawn_needs_watering

A Python automation project that determines whether my lawn in Louisville, KY needs watering based on recent rainfall, forecast rainfall, temperature/dew point conditions, and manually confirmed watering events.

The project runs automatically each morning through GitHub Actions and sends an email only when watering is recommended.

## What It Does

Each run:

1. Pulls weather data from Open-Meteo for the configured latitude/longitude.
2. Calculates rainfall from the past 7 days.
3. Calculates forecast rainfall for the next 3 days.
4. Applies a discounted forecast-rain credit.
5. Adjusts the weekly watering target based on hot/dry or cool/humid conditions.
6. Reads a published Google Sheet of confirmed watering events.
7. Credits recent confirmed watering.
8. Produces one of four recommendations:
   - doesn't need watering
   - needs light watering
   - needs watering
   - needs heavy watering
9. Sends an email only if watering is recommended.
10. Includes a one-click link to confirm watering after it is done.

## Current Model

The baseline weekly target is 1.25 inches of water.

The deficit is calculated approximately as:

```text
water_deficit =
    adjusted_weekly_target
  - recent_rain
  - confirmed_watering_credit
  - discounted_forecast_rain
```

Confirmed watering currently counts as one full weekly watering credit for each unique recent watering-confirmation date.

## Automation

The GitHub Actions workflow runs daily at:

```text
9:00 AM Eastern during daylight saving time
```

The workflow can also be run manually from the GitHub Actions tab.

## Email Notifications

Emails are sent only when the recommendation is:

- needs light watering
- needs watering
- needs heavy watering

If the lawn does not need watering, no email is sent.

The email includes a one-click confirmation link. After watering, clicking that link records the event in a Google Sheet. Future runs use that record to avoid repeated unnecessary watering reminders.

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
config.py                       Configuration values and thresholds
requirements.txt                Python dependencies
data/watering_history.csv        Local recommendation history
.github/workflows/daily_run.yml  GitHub Actions schedule
```

## Future Improvements

Possible later improvements:

- seasonal dormancy suppression
- sprinkler runtime calibration
- HTML email formatting
- evapotranspiration modeling
- dashboard/visualization
- improved duplicate-notification suppression