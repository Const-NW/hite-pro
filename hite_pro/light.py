"""Light platform for HiTE-PRO integration."""
from __future__ import annotations

from homeassistant.components.light import LightEntity
from homeassistant.components import mqtt
from homeassistant.core import callback
import homeassistant.util.color as color_util

from .const import DOMAIN

class HiteProLight(LightEntity):
    """Representation of a HiTE-PRO light."""

    def __init__(self, hass, config):
        """Initialize the light."""
        self.hass = hass
        self._config = config
        self._attr_unique_id = config["unique_id"]
        self._attr_name = config["name"]
        self._state_topic = config.get("state_topic")
        self._command_topic = config["command_topic"]
        self._payload_on = config.get("payload_on", "1")
        self._payload_off = config.get("payload_off", "0")
        self._attr_device_info = {"identifiers": {(DOMAIN, config["device_id"])}}
        self._attr_is_on = False
        self._brightness = None
        self._sub_state = None

        # RGB support if configured
        self._rgb_topic = config.get("rgb_command_topic")
        self._rgb_value_template = config.get("rgb_value_template")

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT events."""
        @callback
        def message_received(msg):
            """Handle new MQTT messages."""
            payload = msg.payload
            
            if payload == self._payload_on:
                self._attr_is_on = True
            elif payload == self._payload_off:
                self._attr_is_on = False
            elif payload.isdigit():
                self._brightness = int(payload)
            
            self.async_write_ha_state()

        if self._state_topic:
            self._sub_state = await mqtt.async_subscribe(
                self.hass, self._state_topic, message_received, 0
            )

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if kwargs.get("brightness") is not None:
            brightness = int(kwargs["brightness"])
            await mqtt.async_publish(
                self.hass,
                self._command_topic,
                str(brightness),
                qos=0,
                retain=True,
            )
            self._brightness = brightness
        elif kwargs.get("rgb_color") is not None and self._rgb_topic:
            rgb = kwargs["rgb_color"]
            await mqtt.async_publish(
                self.hass,
                self._rgb_topic,
                f"{rgb[0]},{rgb[1]},{rgb[2]}",
                qos=0,
                retain=True,
            )
        else:
            await mqtt.async_publish(
                self.hass,
                self._command_topic,
                self._payload_on,
                qos=0,
                retain=True,
            )
        
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await mqtt.async_publish(
            self.hass,
            self._command_topic,
            self._payload_off,
            qos=0,
            retain=True,
        )
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    async def async_will_remove_from_hass(self):
        """Unsubscribe from MQTT events."""
        if self._sub_state:
            self._sub_state()
