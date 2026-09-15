"""General constants for the SAMSON TROVIS integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "samson_trovis"
MANUFACTURER = "Samson"
DEFAULT_NAME = "Samson Trovis"

CONF_PORT_URL = "port_url"
CONF_SLAVE_ID = "slave_id"
CONF_MODEL = "model"
CONF_SLUG = "slug"
CONF_ENABLED_AREAS = "enabled_areas"

MAX_REGISTERS_PER_READ = 50
MAX_COILS_PER_READ = 50

DEFAULT_SLAVE_ID = 246
DEFAULT_SCAN_INTERVAL_SECONDS = 30
DEFAULT_BAUDRATE = 19200
DEFAULT_BYTESIZE = 8
DEFAULT_PARITY = "N"
DEFAULT_STOPBITS = 1
DEFAULT_TIMEOUT = 3

CONTROLLER_MODEL_REGISTER = 0

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]
