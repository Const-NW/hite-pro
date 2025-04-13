"""Config flow for HiTE-PRO integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_MQTT_TOPIC, DEFAULT_TOPIC

class HiteProConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HiTE-PRO integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if not user_input[CONF_MQTT_TOPIC].strip():
                errors["base"] = "invalid_topic"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title="HiTE-PRO Devices",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MQTT_TOPIC, default=DEFAULT_TOPIC): str,
            }),
            errors=errors,
        )