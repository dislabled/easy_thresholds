"""Config flow for Easy Thresholds integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    THRESHOLD_LEVELS,
    RESOLUTION_AUTOMATIC,
    RESOLUTION_MANUAL,
    ATTR_S_MINUS_MINUS,
    ATTR_S_MINUS,
    ATTR_S_PLUS,
    ATTR_S_PLUS_PLUS,
    ATTR_ACTIVE_THRESHOLDS,
    ATTR_RESOLUTION_MODE,
)

SETUP_ENTRY_ID = "setup"


class EasyThresholdsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Easy Thresholds."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step - create setup entry if needed."""
        # Check if setup entry already exists
        setup_entry = None
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get("setup"):
                setup_entry = entry
                break

        if not setup_entry:
            # First time - create setup entry
            if user_input is not None:
                await self.async_set_unique_id(SETUP_ENTRY_ID)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Easy Thresholds",
                    data={"setup": True},
                )

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Optional("dummy"): str,
                    }
                ),
            )

        # Setup exists, add a sensor instead
        errors = {}

        if user_input is not None:
            # Get values with proper type checking
            sensor_entity: str | None = user_input.get("sensor_entity")
            s_minus_minus: float | None = user_input.get(ATTR_S_MINUS_MINUS)
            s_minus: float | None = user_input.get(ATTR_S_MINUS)
            s_plus: float | None = user_input.get(ATTR_S_PLUS)
            s_plus_plus: float | None = user_input.get(ATTR_S_PLUS_PLUS)

            # Validate all values exist and are in correct order
            if (
                sensor_entity is None
                or s_minus_minus is None
                or s_minus is None
                or s_plus is None
                or s_plus_plus is None
                or not (s_minus_minus < s_minus < s_plus < s_plus_plus)
            ):
                errors["base"] = "invalid_thresholds"
            else:
                # Check if this sensor is already configured
                await self.async_set_unique_id(sensor_entity)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=sensor_entity,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_sensor_schema(),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return EasyThresholdsOptionsFlow()

    def _get_sensor_schema(self):
        """Get schema for sensor configuration."""
        return vol.Schema(
            {
                vol.Required("sensor_entity"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(ATTR_S_MINUS_MINUS, default=-10): vol.Coerce(float),
                vol.Required(ATTR_S_MINUS, default=0): vol.Coerce(float),
                vol.Required(ATTR_S_PLUS, default=100): vol.Coerce(float),
                vol.Required(ATTR_S_PLUS_PLUS, default=110): vol.Coerce(float),
                vol.Required(
                    ATTR_ACTIVE_THRESHOLDS, default=["s_minus", "s_plus"]
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=THRESHOLD_LEVELS,
                        multiple=True,
                    )
                ),
                vol.Required(
                    ATTR_RESOLUTION_MODE, default=RESOLUTION_AUTOMATIC
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            RESOLUTION_AUTOMATIC,
                            RESOLUTION_MANUAL,
                        ],
                    )
                ),
            }
        )


class EasyThresholdsOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Easy Thresholds."""

    async def async_step_init(self, user_input=None):
        """Handle options flow - edit sensor configuration."""
        # If this is a setup entry, no options available
        if self.config_entry.data.get("setup"):
            return self.async_abort(reason="no_options")

        if user_input is not None:
            # Validate thresholds
            s_minus_minus = user_input.get(ATTR_S_MINUS_MINUS)
            s_minus = user_input.get(ATTR_S_MINUS)
            s_plus = user_input.get(ATTR_S_PLUS)
            s_plus_plus = user_input.get(ATTR_S_PLUS_PLUS)

            if not (s_minus_minus < s_minus < s_plus < s_plus_plus):
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._get_options_schema(),
                    errors={"base": "invalid_thresholds"},
                )

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self):
        """Get schema for options."""
        current_data = self.config_entry.data

        return vol.Schema(
            {
                vol.Required(
                    ATTR_S_MINUS_MINUS,
                    default=current_data.get(ATTR_S_MINUS_MINUS, -10),
                ): vol.Coerce(float),
                vol.Required(
                    ATTR_S_MINUS, default=current_data.get(ATTR_S_MINUS, 0)
                ): vol.Coerce(float),
                vol.Required(
                    ATTR_S_PLUS, default=current_data.get(ATTR_S_PLUS, 100)
                ): vol.Coerce(float),
                vol.Required(
                    ATTR_S_PLUS_PLUS, default=current_data.get(ATTR_S_PLUS_PLUS, 110)
                ): vol.Coerce(float),
                vol.Required(
                    ATTR_ACTIVE_THRESHOLDS,
                    default=current_data.get(
                        ATTR_ACTIVE_THRESHOLDS, ["s_minus", "s_plus"]
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=THRESHOLD_LEVELS,
                        multiple=True,
                    )
                ),
                vol.Required(
                    ATTR_RESOLUTION_MODE,
                    default=current_data.get(
                        ATTR_RESOLUTION_MODE, RESOLUTION_AUTOMATIC
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            RESOLUTION_AUTOMATIC,
                            RESOLUTION_MANUAL,
                        ],
                    )
                ),
            }
        )
