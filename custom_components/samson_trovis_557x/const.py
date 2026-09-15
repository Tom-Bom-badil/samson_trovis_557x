"""Constants for the Trovis 557x integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "trovis557x"

CONF_CONNECTION: Final = "connection"
CONF_CONNECTION_TYPE: Final = "type"
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_FRAMER: Final = "framer"
CONF_DEVICE: Final = "device"
CONF_BAUDRATE: Final = "baudrate"
CONF_BYTESIZE: Final = "bytesize"
CONF_PARITY: Final = "parity"
CONF_STOPBITS: Final = "stopbits"
CONNECTION_TYPE_TCP: Final = "tcp"
CONNECTION_TYPE_SERIAL: Final = "serial"

FRAMER_SOCKET: Final = "socket"
FRAMER_RTU: Final = "rtu"

CONF_UNIT_ID: Final = "unit_id"
CONF_SLUG: Final = "slug"
CONF_ACCESS_CODE: Final = "access_code"
CONF_MODEL: Final = "model"
CONF_DETECTED_SENSORS: Final = "detected_sensors"
CONF_EXCLUDED_REGISTERS: Final = "excluded_registers"
CONF_EXCLUDED_COILS: Final = "excluded_coils"
DEFAULT_PORT: Final = 502
DEFAULT_FRAMER: Final = FRAMER_SOCKET
SERIAL_BAUDRATES: Final = (19200, 9600)
DEFAULT_BAUDRATE: Final = 19200
DEFAULT_BYTESIZE: Final = 8
DEFAULT_PARITY: Final = "N"
DEFAULT_STOPBITS: Final = 1
DEFAULT_UNIT_ID: Final = 246
DEFAULT_SLUG: Final = "trovis"
# A heating controller is not an express train.
SCAN_INTERVAL: Final = timedelta(seconds=60)
