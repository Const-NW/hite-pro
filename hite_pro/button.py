"""Button platform for HiTE-PRO integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.components import mqtt
from homeassistant.core import callback

from .const import DOMAIN

class HiteProButton(ButtonEntity):
    """Representation of a HiTE-PRO button."""

    def __init__(self, hass, config):
        """Initialize the button."""
        self.hass = hass
        self._config = config
        self._attr_unique_id = config["unique_id"]
        self._attr_name = config["name"]
        self._command_topic = config["command_topic"]
        self._payload_press = config.get("payload_press", "1")
        self._attr_device_info = {"identifiers": {(DOMAIN, config["device_id"])}}

    async def async_press(self) -> None:
        """Handle the button press."""
        await mqtt.async_publish(
            self.hass,
            self._command_topic,
            self._payload_press,
            qos=0,
            retain=False,
        )
