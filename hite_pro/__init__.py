"""
Custom integration for HiTE-PRO devices with automatic discovery.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, SOURCE_IMPORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo, async_get as async_get_device_registry
from homeassistant.components import mqtt
from homeassistant.components.button import ButtonEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.light import LightEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity

_LOGGER = logging.getLogger(__name__)

DOMAIN = "hite_pro"
PLATFORMS = ["button", "switch", "light", "sensor", "binary_sensor"]

CONF_MQTT_TOPIC = "mqtt_topic"
DEFAULT_TOPIC = "/devices/hite-pro/controls/#"

TOPIC_PATTERNS = {
    "button": re.compile(r"^/devices/hite-pro/controls/(Reload)$"),
    "switch": re.compile(r"^/devices/hite-pro/controls/(Relay-\w+_\w+_\d+)$"),
    "light": re.compile(r"^/devices/hite-pro/controls/(Relay-\w+_\w+_\d+.*)$"),
    "binary_sensor": re.compile(r"^/devices/hite-pro/controls/(Smart-\w+_\w+_\w+)$"),
    "sensor": re.compile(r"^/devices/hite-pro/controls/(\w+-\w+_\w+_\w+.*)$"),
}

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_MQTT_TOPIC, default=DEFAULT_TOPIC): str,
})

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

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the HiTE-PRO component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HiTE-PRO from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    mqtt_topic = entry.data.get(CONF_MQTT_TOPIC, DEFAULT_TOPIC)
    await setup_mqtt_discovery(hass, mqtt_topic, entry)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def setup_mqtt_discovery(hass: HomeAssistant, mqtt_topic: str, entry: ConfigEntry):
    """Set up MQTT discovery for HiTE-PRO devices."""
    @callback
    async def async_message_received(msg: mqtt.ReceiveMessage) -> None:
        """Process incoming MQTT message for discovery."""
        topic = msg.topic
        payload = msg.payload
        
        _LOGGER.debug(f"Processing MQTT message: {topic} {payload}")
        
        for platform, pattern in TOPIC_PATTERNS.items():
            if match := pattern.match(topic):
                await process_discovered_device(hass, entry, platform, match.group(1), topic)
                break

    await mqtt.async_subscribe(hass, mqtt_topic, async_message_received)

async def process_discovered_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    platform: str,
    control_name: str,
    topic: str
):
    """Process a discovered device and create appropriate entities."""
    device_id_parts = control_name.split("_")
    
    if control_name == "Reload":
        device_id = "Gateway"
        model = "Gateway"
    else:
        device_id = "_".join(device_id_parts[:2])
        model = device_id_parts[0]
    
    dev_reg = async_get_device_registry(hass)
    device = dev_reg.async_get_device(identifiers={(DOMAIN, device_id)})
    
    if not device:
        device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "manufacturer": "HiTE-PRO",
            "name": device_id.replace("_", " "),
            "model": model,
            "configuration_url": "http://hitepro.local/",
        }
        
        if device_id == "Gateway":
            device_info.update({
                "manufacturer": "HiTE-PRO",
                "model": "Gateway",
                "name": "Gateway",
            })
        
        device = dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            **device_info
        )
    
    entity_config = {
        "unique_id": f"{device_id}_{control_name}",
        "name": control_name.replace("_", " "),
        "state_topic": topic,
        "device_id": device.id,
    }
    
    if platform == "button":
        entity_config.update({
            "command_topic": f"{topic}/on",
            "payload_press": "1",
        })
    elif platform == "switch":
        entity_config.update({
            "command_topic": f"{topic}/on",
            "payload_on": "1",
            "payload_off": "0",
        })
    elif platform == "light":
        entity_config.update({
            "command_topic": f"{topic}/on",
            "payload_on": "1",
            "payload_off": "0",
        })
        if "brightness" in control_name.lower():
            entity_config.update({
                "brightness_command_topic": f"{topic}/on",
                "brightness_scale": 100,
            })
    elif platform == "binary_sensor":
        entity_config.update({
            "payload_on": "1",
            "payload_off": "0",
        })
    
    await add_entity(hass, platform, entity_config)

async def add_entity(hass: HomeAssistant, platform: str, config: dict[str, Any]):
    """Add a new entity to the appropriate platform."""
    if platform == "button":
        entity = HiteProButton(hass, config)
    elif platform == "switch":
        entity = HiteProSwitch(hass, config)
    elif platform == "light":
        entity = HiteProLight(hass, config)
    elif platform == "sensor":
        entity = HiteProSensor(hass, config)
    elif platform == "binary_sensor":
        entity = HiteProBinarySensor(hass, config)
    else:
        return

    platform_entity = hass.data[DOMAIN].get(platform)
    if platform_entity:
        await platform_entity.async_add_entities([entity])

# [Классы сущностей HiteProButton, HiteProSwitch, HiteProLight, 
#  HiteProSensor и HiteProBinarySensor остаются без изменений]

class HiteProButton(ButtonEntity):
    """Representation of a HiTE-PRO button."""

    def __init__(self, hass: HomeAssistant, config: dict):
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

class HiteProSwitch(SwitchEntity):
    """Representation of a HiTE-PRO switch."""

    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialize the switch."""
        self.hass = hass
        self._config = config
        self._attr_unique_id = config["unique_id"]
        self._attr_name = config["name"]
        self._state_topic = config["state_topic"]
        self._command_topic = config["command_topic"]
        self._payload_on = config.get("payload_on", "1")
        self._payload_off = config.get("payload_off", "0")
        self._attr_device_info = {"identifiers": {(DOMAIN, config["device_id"])}}
        self._attr_is_on = False
        self._sub_state = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT events when added to hass."""
        @callback
        def message_received(msg: mqtt.ReceiveMessage) -> None:
            """Handle new MQTT messages."""
            payload = msg.payload
            if payload == self._payload_on:
                self._attr_is_on = True
            elif payload == self._payload_off:
                self._attr_is_on = False
            self.async_write_ha_state()

        self._sub_state = await mqtt.async_subscribe(
            self.hass, self._state_topic, message_received, 0
        )

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
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
        """Turn the switch off."""
        await mqtt.async_publish(
            self.hass,
            self._command_topic,
            self._payload_off,
            qos=0,
            retain=True,
        )
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Unsubscribe from MQTT events."""
        if self._sub_state:
            self._sub_state()

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

        if "brightness_command_topic" in config:
            self._brightness_topic = config["brightness_command_topic"]
            self._brightness_scale = config.get("brightness_scale", 100)

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT events when added to hass."""
        @callback
        def message_received(msg: mqtt.ReceiveMessage) -> None:
            """Handle new MQTT messages."""
            payload = msg.payload
            if payload == self._payload_on:
                self._attr_is_on = True
            elif payload == self._payload_off:
                self._attr_is_on = False
            elif payload.isdigit():
                self._brightness = int(payload) * 255 / self._brightness_scale
            self.async_write_ha_state()

        if self._state_topic:
            self._sub_state = await mqtt.async_subscribe(
                self.hass, self._state_topic, message_received, 0
            )

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if kwargs.get("brightness") is not None and hasattr(self, '_brightness_topic'):
            brightness = int(kwargs["brightness"] * self._brightness_scale / 255)
            await mqtt.async_publish(
                self.hass,
                self._brightness_topic,
                str(brightness),
                qos=0,
                retain=True,
            )
            self._brightness = kwargs["brightness"]
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
        """Return the brightness of this light between 0..255."""
        return self._brightness

    async def async_will_remove_from_hass(self):
        """Unsubscribe from MQTT events."""
        if self._sub_state:
            self._sub_state()

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
        """Subscribe to MQTT events when added to hass."""
        @callback
        def message_received(msg: mqtt.ReceiveMessage) -> None:
            """Handle new MQTT messages."""
            self._attr_native_value = msg.payload
            self.async_write_ha_state()

        self._sub_state = await mqtt.async_subscribe(
            self.hass, self._state_topic, message_received, 0
        )

    async def async_will_remove_from_hass(self):
        """Unsubscribe from MQTT events."""
        if self._sub_state:
            self._sub_state()

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
        """Subscribe to MQTT events when added to hass."""
        @callback
        def message_received(msg: mqtt.ReceiveMessage) -> None:
            """Handle new MQTT messages."""
            payload = msg.payload
            if payload == self._payload_on:
                self._attr_is_on = True
            elif payload == self._payload_off:
                self._attr_is_on = False
            self.async_write_ha_state()

        self._sub_state = await mqtt.async_subscribe(
            self.hass, self._state_topic, message_received, 0
        )

    async def async_will_remove_from_hass(self):
        """Unsubscribe from MQTT events."""
        if self._sub_state:
            self._sub_state()

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
