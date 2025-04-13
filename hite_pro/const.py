"""Constants for HiTE-PRO integration."""
from typing import Final
import re

DOMAIN: Final = "hite_pro"
PLATFORMS: Final = ["button", "switch", "light", "sensor", "binary_sensor"]

CONF_MQTT_TOPIC: Final = "mqtt_topic"
DEFAULT_TOPIC: Final = "/devices/hite-pro/controls/#"

TOPIC_PATTERNS: Final = {
    "button": re.compile(r"^/devices/hite-pro/controls/(Reload)$"),
    "switch": re.compile(r"^/devices/hite-pro/controls/(Relay-\w+_\w+_\d+)$"),
    "light": re.compile(r"^/devices/hite-pro/controls/(Relay-\w+_\w+_\d+.*)$"),
    "binary_sensor": re.compile(r"^/devices/hite-pro/controls/(Smart-\w+_\w+_\w+)$"),
    "sensor": re.compile(r"^/devices/hite-pro/controls/(\w+-\w+_\w+_\w+.*)$"),
}
