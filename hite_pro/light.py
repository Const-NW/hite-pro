"""Light platform for HiTE-PRO integration."""
from __future__ import annotations

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HiTE-PRO light platform."""
    # В реальной реализации здесь должна быть логика создания светильников
    async_add_entities([HiteProLight(hass, {
        "unique_id": "test_light",
        "name": "Test Light",
        "state_topic": "/devices/hite-pro/controls/Light1",
        "command_topic": "/devices/hite-pro/controls/Light1/on",
        "payload_on": "1",
        "payload_off": "0",
        "device_id": "light1"
    })])

class HiteProLight(LightEntity):
    """Representation of a HiTE-PRO light."""

    def __init__(self, hass: HomeAssistant, config: dict):
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
            self._sub_state = await self.hass.components.mqtt.async_subscribe(
                self.hass, self._state_topic, message_received, 0
            )

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if kwargs.get("brightness") is not None:
            brightness = kwargs["brightness"]
            await self.hass.components.mqtt.async_publish(
                self.hass,
                self._command_topic,
                str(brightness),
                qos=0,
                retain=True,
            )
            self._brightness = brightness
        else:
            await self.hass.components.mqtt.async_publish(
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
        await self.hass.components.mqtt.async_publish(
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