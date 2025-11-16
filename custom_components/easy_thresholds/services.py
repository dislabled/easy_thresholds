"""Services for Easy Thresholds integration."""

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    _LOGGER,
    SERVICE_CLEAR_ALARM,
    ATTR_ALARM_NAME,
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Easy Thresholds."""

    async def clear_alarm_service(call: ServiceCall) -> None:
        """Handle clear alarm service call."""
        alarm_name = call.data.get(ATTR_ALARM_NAME)

        if not alarm_name:
            _LOGGER.error("clear_alarm service called without alarm_name")
            return

        # Get the alarm monitor sensor
        alarm_monitor = hass.data.get(DOMAIN, {}).get("alarm_monitor")
        if not alarm_monitor:
            _LOGGER.error("Alarm monitor sensor not found")
            return

        # Check if alarm is in safe range before allowing clear
        if not alarm_monitor.can_clear_alarm(alarm_name):
            _LOGGER.warning(
                f"Cannot clear alarm {alarm_name}: sensor not in safe range"
            )
            return

        alarm_monitor.clear_alarm(alarm_name)

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_ALARM,
        clear_alarm_service,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ALARM_NAME): cv.string,
            }
        ),
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_CLEAR_ALARM)
