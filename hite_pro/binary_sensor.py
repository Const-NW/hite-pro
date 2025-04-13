"""Binary sensor platform for HiTE-PRO integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HiTE-PRO binary sensor platform."""
    # В реальной реализации здесь должна быть логика создания бинарных сенсоров
    async_add_entities([HiteProBinarySensor(hass, {
        "unique_id": "test_binary_sensor",
        "name": "Test Motion",
        "state_topic": "/devices/hite-pro/controls/Motion",
        "payload_on": "1",
        "payload_off": "0",
        "device_class": "motion",
        "device_id": "motion1"
    })])

class HiteProBinarySensor(BinarySensorEntity):
    """Representation of a HiTE-PRO binary sensor."""

    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialize the binary sensor."""
        self.hass = hass
        self._config = config
        self._attr_unique_id = config["unique_id"]
        self._attr_name = config["name"]
        self._state_topic = config["state_topic"]
        self._payload_on = config.get("payload_on", "1")
        self._payload_off = config.get("payload_off", "0")
        self._attr_device_class = config.get("device_class")
        self._attr_device_info = {"identifiers": {(DOMAIN, config["device_id"])}}
        self._attr_is_on = False
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
            self.async_write_ha_state()

        self._sub_state = await self.hass.components.mqtt.async_subscribe(
            self.hass, self._state_topic, message_received, 0
        )

    async def async_will_remove_from_hass(self):
        """Unsubscribe from MQTT events."""
        if self._sub_state:
            self._sub_state()