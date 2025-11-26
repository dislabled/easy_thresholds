"""Sensor for Easy Thresholds integration."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_ACTIVE_ALARMS,
    ATTR_ALARM_NAME,
    ATTR_TIMESTAMP,
    ATTR_THRESHOLD_VALUE,
    ATTR_S_MINUS_MINUS,
    ATTR_S_MINUS,
    ATTR_S_PLUS,
    ATTR_S_PLUS_PLUS,
    ATTR_ACTIVE_THRESHOLDS,
    ATTR_RESOLUTION_MODE,
    ICON_ALARM_MONITOR,
    THRESHOLD_CRITICAL_LOW,
    THRESHOLD_WARNING_LOW,
    THRESHOLD_WARNING_HIGH,
    THRESHOLD_CRITICAL_HIGH,
    RESOLUTION_AUTOMATIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Easy Thresholds sensor from config entry."""
    # Only create the main sensor for the setup entry
    if not config_entry.data.get("setup"):
        return

    sensor = AlarmMonitorSensor(hass, config_entry)

    # Store reference for services
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["alarm_monitor"] = sensor

    async_add_entities([sensor], True)


class AlarmMonitorSensor(SensorEntity):
    """Main alarm monitor sensor entity."""

    def __init__(self, hass: HomeAssistant, config_entry):
        """Initialize the sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self._active_alarms: List[Dict[str, Any]] = []
        self._sensor_configs: Dict[str, Dict[str, Any]] = {}
        self._binary_sensors: List[Dict[str, str]] = []
        self._last_notified_alarms: set = set()  # Track notified alarms for debouncing

        # Parse configuration
        self._parse_config(config_entry.data)

        self._attr_name = "Easy Thresholds"
        # Use fixed unique_id so only one sensor is created across all entries
        self._attr_unique_id = f"{DOMAIN}_alarm_monitor"
        self._attr_icon = ICON_ALARM_MONITOR

    def _parse_config(self, config_data: Dict[str, Any]) -> None:
        """Parse configuration data from all entries."""
        # Always collect sensors from all current config entries
        self._sensor_configs.clear()
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            sensor_entity = entry.data.get("sensor_entity")
            if sensor_entity:
                # Convert to dict to avoid MappingProxyType issues
                self._sensor_configs[sensor_entity] = dict(entry.data)

    async def async_added_to_hass(self) -> None:
        """Subscribe to sensor state changes and config entry updates."""
        # Parse config to get all current sensors from all entries
        self._parse_config(self.config_entry.data)

        # Add update listeners for all entries in our domain
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            self.async_on_remove(entry.add_update_listener(self._async_on_entry_update))

        # Track ALL state changes for our sensors
        self.async_on_remove(
            self.hass.bus.async_listen(
                "state_changed",
                self._on_any_state_change,
            )
        )

    async def _async_on_entry_update(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Handle config entry update - re-check alarms with new thresholds."""
        # Re-parse to get new thresholds
        self._parse_config(self.config_entry.data)

        # Get the sensor that was updated
        sensor_entity = entry.data.get("sensor_entity")
        if sensor_entity:
            # Check current state against new thresholds
            state = self.hass.states.get(sensor_entity)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    value = float(state.state)
                    config = self._sensor_configs.get(sensor_entity)
                    if config:
                        # Re-check with new thresholds - this will clear or create alarms as needed
                        self._check_numeric_sensor(sensor_entity, value, config)
                except (ValueError, TypeError):
                    pass

        self.async_write_ha_state()

    @callback
    def _on_any_state_change(self, event) -> None:
        """Listen to all state changes and filter for our sensors."""
        entity_id = event.data.get("entity_id")
        if not entity_id:
            return

        # Re-parse to check all latest entries
        self._parse_config(self.config_entry.data)

        new_state = event.data.get("new_state")
        if new_state is None:
            return

        # Handle numeric sensors
        if entity_id in self._sensor_configs:
            try:
                value = float(new_state.state)
            except (ValueError, TypeError):
                return

            config = self._sensor_configs.get(entity_id)
            if config:
                self._check_numeric_sensor(entity_id, value, config)
                self.async_write_ha_state()

        # Handle binary sensors
        for bs in self._binary_sensors:
            if bs["entity"] == entity_id:
                is_alarmed = new_state.state == "on"
                alarm_name: str = bs.get("name") or entity_id

                if is_alarmed:
                    self._create_alarm(
                        alarm_name=alarm_name,
                        threshold_value=None,
                        sensor_entity=entity_id,
                    )
                else:
                    self._clear_alarm_by_name(alarm_name)

                self.async_write_ha_state()
                break

    @callback
    def _on_binary_sensor_state_change(self, event) -> None:
        """Handle binary sensor state changes."""
        entity_id = event.data["entity_id"]
        new_state = event.data["new_state"]

        if new_state is None:
            return

        # Find the binary sensor config
        bs_config = None
        for bs in self._binary_sensors:
            if bs["entity"] == entity_id:
                bs_config = bs
                break

        if not bs_config:
            return

        # Trigger alarm if binary sensor is "on"
        is_alarmed = new_state.state == "on"
        alarm_name: str = bs_config.get("name") or entity_id

        if is_alarmed:
            self._create_alarm(
                alarm_name=alarm_name,
                threshold_value=None,
                sensor_entity=entity_id,
            )
        else:
            # Clear binary sensor alarm
            self._clear_alarm_by_name(alarm_name)

        self.async_write_ha_state()

    def _check_numeric_sensor(
        self, entity_id: str, value: float, config: Dict[str, Any]
    ) -> None:
        """Check numeric sensor against thresholds."""
        s_minus_minus = config[ATTR_S_MINUS_MINUS]
        s_minus = config[ATTR_S_MINUS]
        s_plus = config[ATTR_S_PLUS]
        s_plus_plus = config[ATTR_S_PLUS_PLUS]
        active_thresholds = config[ATTR_ACTIVE_THRESHOLDS]
        resolution_mode = config[ATTR_RESOLUTION_MODE]

        # Determine which thresholds are triggered
        triggered_thresholds = []

        if value < s_minus_minus and THRESHOLD_CRITICAL_LOW in active_thresholds:
            triggered_thresholds.append(THRESHOLD_CRITICAL_LOW)
        elif (
            s_minus_minus <= value < s_minus
            and THRESHOLD_WARNING_LOW in active_thresholds
        ):
            triggered_thresholds.append(THRESHOLD_WARNING_LOW)

        if value > s_plus_plus and THRESHOLD_CRITICAL_HIGH in active_thresholds:
            triggered_thresholds.append(THRESHOLD_CRITICAL_HIGH)
        elif (
            s_plus < value <= s_plus_plus
            and THRESHOLD_WARNING_HIGH in active_thresholds
        ):
            triggered_thresholds.append(THRESHOLD_WARNING_HIGH)

        # Check if in safe range
        in_safe_range = s_minus <= value <= s_plus

        # Handle triggered thresholds
        for threshold in triggered_thresholds:
            alarm_name = f"{entity_id}_{threshold}"
            if not self._alarm_exists(alarm_name):
                self._create_alarm(
                    alarm_name=alarm_name,
                    threshold_value=threshold,
                    sensor_entity=entity_id,
                )

        # Handle automatic resolution
        if resolution_mode == RESOLUTION_AUTOMATIC and in_safe_range:
            # Clear all alarms for this sensor
            self._clear_alarms_by_sensor(entity_id)

    def _alarm_exists(self, alarm_name: str) -> bool:
        """Check if alarm already exists."""
        return any(
            alarm[ATTR_ALARM_NAME] == alarm_name for alarm in self._active_alarms
        )

    def _create_alarm(
        self,
        alarm_name: str,
        threshold_value: str | None,
        sensor_entity: str,
    ) -> None:
        """Create a new alarm."""
        alarm = {
            ATTR_ALARM_NAME: alarm_name,
            ATTR_TIMESTAMP: datetime.now().isoformat(),
            ATTR_THRESHOLD_VALUE: threshold_value,
        }

        self._active_alarms.append(alarm)

        # Send notification
        self._send_notification(alarm_name, sensor_entity, threshold_value)

    def _clear_alarm_by_name(self, alarm_name: str) -> None:
        """Clear alarm by name."""
        self._active_alarms = [
            a for a in self._active_alarms if a[ATTR_ALARM_NAME] != alarm_name
        ]
        # Remove from debounce tracking
        self._last_notified_alarms.discard(alarm_name)

    def _clear_alarms_by_sensor(self, sensor_entity: str) -> None:
        """Clear all alarms for a sensor."""
        # Collect alarm names to remove from debounce tracking
        alarms_to_clear = [
            a[ATTR_ALARM_NAME]
            for a in self._active_alarms
            if a[ATTR_ALARM_NAME].startswith(sensor_entity)
        ]

        self._active_alarms = [
            a
            for a in self._active_alarms
            if not a[ATTR_ALARM_NAME].startswith(sensor_entity)
        ]

        # Remove from debounce tracking
        for alarm_name in alarms_to_clear:
            self._last_notified_alarms.discard(alarm_name)

    def _send_notification(
        self, alarm_name: str, sensor_entity: str, threshold_value: Optional[str]
    ) -> None:
        """Send persistent notification."""
        # Debounce: only notify if not already notified
        if alarm_name in self._last_notified_alarms:
            return

        self._last_notified_alarms.add(alarm_name)

        title = f"Alarm: {alarm_name}"
        message = (
            f"Sensor: {sensor_entity}\nThreshold: {threshold_value or 'binary_alert'}"
        )

        self.hass.async_create_task(
            self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": message,
                    "title": title,
                    "notification_id": f"easy_thresholds_{alarm_name}",
                },
            )
        )

    @property
    def native_value(self) -> str:
        """Return the state (number of active alarms)."""
        return str(len(self._active_alarms))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        return {
            ATTR_ACTIVE_ALARMS: self._active_alarms,
        }

    def can_clear_alarm(self, alarm_name: str) -> bool:
        """Check if alarm can be cleared (sensor in safe range)."""
        # For binary sensor alarms, always allow clearing
        for bs in self._binary_sensors:
            if bs.get("name") == alarm_name or bs["entity"] == alarm_name:
                return True

        # For numeric sensor alarms, check if sensor is in safe range
        for entity_id, config in self._sensor_configs.items():
            if alarm_name.startswith(entity_id):
                # Get current sensor state
                state = self.hass.states.get(entity_id)
                if state is None or state.state in ("unknown", "unavailable"):
                    return False

                try:
                    value = float(state.state)
                    s_minus = config[ATTR_S_MINUS]
                    s_plus = config[ATTR_S_PLUS]
                    return s_minus <= value <= s_plus
                except (ValueError, TypeError):
                    return False

        return False

    def clear_alarm(self, alarm_name: str) -> None:
        """Clear an alarm by name."""
        self._clear_alarm_by_name(alarm_name)
        if alarm_name in self._last_notified_alarms:
            self._last_notified_alarms.discard(alarm_name)
        self.async_write_ha_state()
