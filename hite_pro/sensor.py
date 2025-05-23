"""Sensor platform for HiTE-PRO integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HiTE-PRO sensor platform."""
    # В реальной реализации здесь должна быть логика создания сенсоров
    async_add_entities([HiteProSensor(hass, {
        "unique_id": "test_sensor",
        "name": "Test Sensor",
        "state_topic": "/devices/hite-pro/controls/Temperature",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "device_id": "sensor1"
    })])

class HiteProSensor(SensorEntity):
    """Representation of a HiTE-PRO sensor."""

    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._attr_unique_id = config["unique_id"]
        self._attr_name = config["name"]
        self._state_topic = config["state_topic"]
        self._attr_device_class = config.get("device_class")
        self._attr_native_unit_of_measurement = config.get("unit_of_measurement")
        self._attr_device_info = {"identifiers": {(DOMAIN, config["device_id"])}}
        self._attr_native_value = None
        self._sub_state = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT events."""
        @callback
        def message_received(msg):
            """Handle new MQTT messages."""
            self._attr_native_value = msg.payload
            self.async_write_ha_state()

        self._sub_state = await self.hass.components.mqtt.async_subscribe(
            self.hass, self._state_topic, message_received, 0
        )

    async def async_will_remove_from_hass(self):
        """Unsubscribe from MQTT events."""
        if self._sub_state:
            self._sub_state()