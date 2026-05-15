# ==================================================
# PROJECT CONFIGURATION
# ==================================================

LATITUDE = 38.2396
LONGITUDE = -85.7340

BASE_WEEKLY_TARGET = 1.25

RECENT_RAIN_DAYS = 7
FORECAST_DAYS = 3

FORECAST_DISCOUNT = 0.70

# ==================================================
# WEATHER STRESS ADJUSTMENTS
# ==================================================

HOT_TEMP_THRESHOLD = 90
VERY_DRY_DEW_POINT_THRESHOLD = 60
HUMID_DEW_POINT_THRESHOLD = 65
COOL_TEMP_THRESHOLD = 75

HOT_DRY_TARGET = 1.50
COOL_HUMID_TARGET = 1.00

# ==================================================
# EMAIL SETTINGS
# ==================================================

EMAIL_RECOMMENDATIONS = [
    "needs light watering",
    "needs watering",
    "needs heavy watering"
]

# ==================================================
# WATERING CONFIRMATION
# ==================================================

WATERING_CONFIRMATION_LINK = "https://script.google.com/macros/s/AKfycbyXiOO4LEAFZwl3jsyYZlgUlbnPTZhtCsjkZLAhR6FH-35eZWOB4y5c6ZqcTrilIpnW/exec"

WATERING_CREDITS = {
    "needs light watering": 0.30,
    "needs watering": 0.70,
    "needs heavy watering": 1.25
}

WATERING_CONFIRMATION_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRU0GzmaNpsllUl2byx-BGTwV-yxLLcb6hCcmmhmmuU1UeoWciGGHhTvM14z0LezCflTtgTI-dUXIyh/pub?output=csv"