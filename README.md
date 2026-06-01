# lawn_needs_watering

A Python home-automation project that determines whether a lawn likely needs watering based on recent rainfall, forecast rainfall, weather conditions, and manually confirmed watering history.

The project automatically retrieves weather data, evaluates watering needs, checks mowing history, and sends email notifications only when action is likely useful.

The workflow runs daily through GitHub Actions and is designed to solve a practical real-world maintenance problem rather than serve as a purely academic exercise.

## What It Does

Each run:

1. Pulls weather data from Open-Meteo.
2. Calculates recent rainfall totals.
3. Calculates forecast rainfall totals.
4. Adjusts watering recommendations for temperature and humidity conditions.
5. Reads confirmed watering history from Google Sheets.
6. Reads mowing history from Google Sheets.
7. Calculates whether watering is likely needed.
8. Calculates whether a mowing reminder is likely useful.
9. Generates a recommendation.
10. Sends an email only when action is recommended.
11. Includes one-click links for recording future lawn-care events.

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

## Author

David Ford

This project was developed by David Ford with AI-assisted coding support (ChatGPT) used for debugging, documentation, workflow planning, and code review. Project design, implementation decisions, validation, interpretation, and final repository contents were reviewed and approved by the author.