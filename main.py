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
# MAIN SCRIPT
# ==================================================

print("Lawn watering project initialized.")

print(f"Latitude: {LATITUDE}")
print(f"Longitude: {LONGITUDE}")

print(f"Weekly target: {BASE_WEEKLY_TARGET} inches")