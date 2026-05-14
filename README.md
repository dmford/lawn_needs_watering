# lawn_needs_watering

A Python automation project that evaluates whether my lawn in Louisville, KY needs watering based on:

- Recent rainfall
- Upcoming forecast rainfall
- Seasonal conditions
- Weather-adjusted watering targets

The script is designed to run automatically through GitHub Actions and produce a simple recommendation:

- Doesn't need watering
- Needs light watering
- Needs watering
- Needs heavy watering

## Planned Features

### Version 1
- Pull historical rainfall data
- Pull forecast rainfall data
- Calculate estimated water deficit
- Generate watering recommendation

### Future Improvements
- Temperature and dew point adjustments
- Seasonal dormancy suppression
- Sprinkler runtime calibration
- Notification system
- Visualization/dashboard
- Evapotranspiration modeling