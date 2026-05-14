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

EMAIL_RECIPIENT = "david.m.ford@outlook.com"

EMAIL_RECOMMENDATIONS = [
    "needs light watering",
    "needs watering",
    "needs heavy watering"
]