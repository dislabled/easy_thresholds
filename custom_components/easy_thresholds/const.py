"""Constants for the Easy Thresholds integration."""

import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "easy_thresholds"
ALARM_MONITOR_ENTITY = "sensor.alarm_monitor"

# Threshold levels
THRESHOLD_CRITICAL_LOW = "s_minus_minus"
THRESHOLD_WARNING_LOW = "s_minus"
THRESHOLD_WARNING_HIGH = "s_plus"
THRESHOLD_CRITICAL_HIGH = "s_plus_plus"

THRESHOLD_LEVELS = [
    THRESHOLD_CRITICAL_LOW,
    THRESHOLD_WARNING_LOW,
    THRESHOLD_WARNING_HIGH,
    THRESHOLD_CRITICAL_HIGH,
]

# Service names
SERVICE_CLEAR_ALARM = "clear_alarm"

# Attribute names
ATTR_ACTIVE_ALARMS = "active_alarms"
ATTR_ALARM_NAME = "alarm_name"
ATTR_TIMESTAMP = "timestamp_triggered"
ATTR_THRESHOLD_VALUE = "threshold_value"
ATTR_SENSOR_ENTITY = "sensor_entity"
ATTR_S_MINUS_MINUS = "s_minus_minus"  # Critical low
ATTR_S_MINUS = "s_minus"  # Warning low
ATTR_S_PLUS = "s_plus"  # Warning high
ATTR_S_PLUS_PLUS = "s_plus_plus"  # Critical high
ATTR_ACTIVE_THRESHOLDS = "active_thresholds"
ATTR_RESOLUTION_MODE = "resolution_mode"
ATTR_BINARY_SENSORS = "binary_sensors"

# Resolution modes
RESOLUTION_AUTOMATIC = "automatic"
RESOLUTION_MANUAL = "manual"

# Icons
ICON_ALARM = "mdi:bell-alert"
ICON_ALARM_MONITOR = "mdi:bell-check"
