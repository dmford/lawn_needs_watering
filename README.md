# Lawn Watering and Mowing Automation

A Python-based home automation project that uses local weather data, historical lawn-maintenance records, and scheduled cloud workflows to generate actionable watering and mowing recommendations.

The system evaluates lawn conditions each day using recent weather, forecast weather, measured irrigation, and user-maintained mowing records. Recommendations are delivered by email only when action is likely to be beneficial.

The project serves as an example of practical automation, decision-support systems, API integration, empirical calibration, and cloud-based scheduling.

## Project Goal

The objective is to automate routine lawn-care decisions using weather data, locally calibrated irrigation measurements, and historical observations.

Rather than manually checking forecasts, estimating rainfall deficits, remembering recent watering, and tracking mowing intervals, the system evaluates these conditions automatically and generates recommendations when intervention is warranted.

The system is designed primarily to support the long-term health of the lawn rather than simply generate reminders on a fixed schedule. Watering recommendations therefore attempt to balance adequate moisture with avoidance of unnecessary or shallow irrigation.

The longer-term goal is to evolve portions of the system from rule-based recommendations into data-driven forecasting tools that learn from accumulated lawn-maintenance observations.

## What It Does

Each daily run:

1. Pulls recent and forecast weather data from Open-Meteo.
2. Calculates rainfall over a rolling seven-day window.
3. Discounts forecast rainfall to account for forecast uncertainty.
4. Adjusts the weekly water target based on temperature and humidity conditions.
5. Reads recorded sprinkler runtimes from Google Sheets and converts them to irrigation depth.
6. Calculates the remaining lawn water deficit.
7. Determines whether the deficit is large enough to justify a meaningful irrigation event.
8. Converts the recommended irrigation depth into sprinkler runtime.
9. Reads mowing history from Google Sheets.
10. Estimates current grass height from the most recent mowing record.
11. Identifies favorable and unfavorable mowing windows using forecast rainfall.
12. Tracks whether weed eating is due with the next mowing.
13. Sends an email only when watering and/or mowing action is recommended.
14. Includes embedded links for recording watering and mowing events.

## Decision Models

### Watering

The baseline weekly water target is **1.25 inches**.

This target is consistent with University of Kentucky Extension guidance for common Kentucky cool-season lawns, which generally indicates approximately **1 to 1.5 inches of moisture per week** while emphasizing that irrigation should respond to actual lawn and weather conditions rather than occur automatically on a fixed schedule.

The approximate water deficit is calculated as:

```text
water_deficit =
    adjusted_weekly_target
  - recent_rain
  - confirmed_watering_credit
  - discounted_forecast_rain
```

The model considers:

* Rainfall during the rolling seven-day period
* Confirmed sprinkler irrigation during the same period
* Discounted rainfall expected during the forecast period
* Recent and forecast temperature conditions
* Recent and forecast dew-point conditions

#### Weather Adjustment

The normal weekly target is 1.25 inches.

The target can be adjusted upward during hot, dry conditions or downward during cool, humid conditions using configurable temperature and dew-point thresholds.

Forecast rainfall receives partial rather than full credit because forecast precipitation is uncertain.

#### Measured Sprinkler Output

Sprinkler irrigation is recorded as **minutes of runtime** rather than subjective categories such as light, medium, or heavy watering.

The sprinkler was empirically calibrated using a catch-cup test. Six identical containers were distributed through the irrigated area and the sprinkler was operated for exactly 15 minutes. The combined measurements corresponded to approximately **1/8 inch of average irrigation in 15 minutes**.

The model therefore uses an estimated sprinkler application rate of:

```text
0.50 inches per hour
```

Recorded sprinkler runtime is converted to estimated irrigation depth:

```text
watering_inches =
    watering_minutes / 60
    * sprinkler_inches_per_hour
```

This calibration makes recorded watering events directly comparable with rainfall measured in inches.

#### Deep and Infrequent Watering

University of Kentucky Extension recommends avoiding frequent, shallow lawn irrigation and instead watering deeply and relatively infrequently. Extension guidance indicates that approximately **1/2 to 1 inch** of water will generally wet the upper several inches of soil, while other UK turf guidance uses approximately **2/3 inch** as a typical substantial irrigation event.

The automation incorporates that principle by using:

```text
Minimum recommended irrigation event: 0.50 inches
Maximum recommended irrigation event: 0.67 inches
```

If the calculated deficit is less than 0.50 inches, the system does not recommend watering yet.

If the deficit is between 0.50 and approximately 0.67 inches, the system recommends enough sprinkler runtime to address the deficit.

If the deficit exceeds approximately 0.67 inches, the current irrigation recommendation is capped at approximately 0.67 inches. Any remaining deficit can be reevaluated during subsequent daily runs rather than attempting to apply an excessive amount in a single session.

At the calibrated sprinkler rate, this produces an approximate recommended runtime range of:

```text
60–80 minutes
```

Runtime recommendations are rounded upward to five-minute increments.

This approach is intended to favor meaningful, deeper watering events rather than frequent surface watering.

### Mowing

Mowing recommendations are based on:

* Last recorded mow date
* Recorded post-mow height
* Estimated daily grass-growth rate
* Preferred mowing height
* Maximum preferred height
* Near-term forecast rainfall
* Recent heavy rainfall
* Weed-eating history

The system estimates current grass height from elapsed time since the most recent mowing and an estimated daily growth rate. It then projects when the grass will reach the preferred mowing height and identifies a primary mowing window around that date.

Forecast rainfall is used to classify potential mowing dates as favorable or unfavorable.

Mowing records are submitted through a Google Apps Script web form and stored in Google Sheets.

Recorded information includes:

* Mowing date
* Pre-mow height measurements at up to five predefined locations
* Calculated average, maximum, minimum, and range of measured heights
* Post-mow height
* Ground condition
* Cut quality
* Clipping handling
* Clipping result
* Whether weed eating was performed
* Reason for mowing
* Optional notes

#### Weed Eating

The mowing logger records whether weed eating was performed during each mowing.

The next mowing recommendation uses the most recent mowing record to determine whether weed eating is due:

```text
Previous mowing included weed eating -> not due
Previous mowing omitted weed eating -> due
```

This provides a simple alternating schedule while preserving the actual maintenance history rather than relying on a separate counter.

## Automation

The system runs automatically through GitHub Actions.

Scheduled execution occurs daily at approximately:

```text
8:30 AM Eastern during daylight saving time
```

The workflow may also be executed manually from the GitHub Actions interface.

## Email Notifications

Emails are sent only when watering and/or mowing action is recommended.

Subject lines are designed to provide the primary action at a glance. Examples include:

```text
[Lawn] Water 65m
[Lawn] Mow Thu–Fri
[Lawn] Water 65m + Mow Thu–Fri
```

The email format is optimized for quick mobile review:

1. Recommended action first.
2. Recommended sprinkler runtime when watering is required.
3. Weed-eating status when mowing is recommended.
4. Embedded logging links near the top.
5. Supporting weather, irrigation, mowing, and scheduling details below.
6. Permanent manual logging links in the footer.

## Technologies Used

* Python
* GitHub Actions
* Open-Meteo API
* Google Sheets
* Google Apps Script
* SMTP email automation

## Repository Structure

```text
main.py                          Main application and decision logic
config.py                        Configuration values and thresholds
requirements.txt                 Python dependencies

data/
    watering_history.csv         Local diagnostic/output history
    mowing_history.csv           Local mowing-history fallback

.github/workflows/
    daily_run.yml                Scheduled GitHub Actions workflow
```

Google Sheets serve as the primary user-maintained source for recorded watering and mowing activity. Local CSV files support logging and fallback behavior where applicable.

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
* Additional calibration using observed lawn condition and soil moisture
* Improved dashboards and visualization tools
* More sophisticated mowing-window forecasting
* Long-term model validation against observed lawn outcomes

## Author

David Ford

This project was developed by David Ford with AI-assisted coding support from ChatGPT for debugging, documentation, workflow planning, implementation support, and code review. Project design, implementation decisions, validation, interpretation, and final repository contents were reviewed and approved by the author.