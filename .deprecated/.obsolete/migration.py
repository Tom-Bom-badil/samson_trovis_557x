"""Config entry migration helpers for the TROVIS 557x integration."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE, CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_CONNECTION_TYPE,
    CONF_DEVICE as TROVIS_CONF_DEVICE,
    CONF_FRAMER,
    CONF_HOST as TROVIS_CONF_HOST,
    CONF_PARITY,
    CONF_PORT as TROVIS_CONF_PORT,
    CONF_STOPBITS,
    CONNECTION_TYPE_SERIAL,
    CONNECTION_TYPE_TCP,
    FRAMER_RTU,
    FRAMER_SOCKET,
)

_LOGGER = logging.getLogger(__name__)

_LEGACY_CONNECTION_ENTRY_ID = "connection_entry_id"
_MODBUS_CONNECTION_DOMAIN = "modbus_connection"
_TARGET_VERSION = 2


def _legacy_connection_entry(
    hass: HomeAssistant,
    entry_id: str,
) -> ConfigEntry | None:
    """Return the legacy Modbus Connection config entry by entry id."""
    return next(
        (
            entry
            for entry in hass.config_entries.async_entries(_MODBUS_CONNECTION_DOMAIN)
            if entry.entry_id == entry_id
        ),
        None,
    )


def _parse_socket_device(device: str) -> tuple[str, int] | None:
    """Parse a legacy pyserial socket:// device as an RTU-over-TCP endpoint."""
    parsed = urlparse(device)
    if parsed.scheme != "socket" or parsed.hostname is None or parsed.port is None:
        return None
    return parsed.hostname, parsed.port


def _migrate_legacy_connection_data(
    legacy_data: dict[str, Any],
) -> dict[str, Any] | None:
    """Convert legacy Modbus Connection data to TROVIS-owned connection data."""
    connection_type = legacy_data.get(CONF_TYPE)

    if connection_type == CONNECTION_TYPE_TCP:
        try:
            return {
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP,
                TROVIS_CONF_HOST: str(legacy_data[CONF_HOST]),
                TROVIS_CONF_PORT: int(legacy_data[CONF_PORT]),
                CONF_FRAMER: FRAMER_SOCKET,
            }
        except (KeyError, TypeError, ValueError):
            return None

    if connection_type == CONNECTION_TYPE_SERIAL:
        try:
            device = str(legacy_data[CONF_DEVICE])
        except (KeyError, TypeError, ValueError):
            return None

        # The legacy provider represented RTU-over-TCP through pyserial's
        # socket:// URL while marking the connection itself as "serial".
        # In modbus-connection 4.x this transport has a first-class model:
        # ModbusTcpParams(..., framer="rtu").
        socket_endpoint = _parse_socket_device(device)
        if socket_endpoint is not None:
            host, port = socket_endpoint
            return {
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP,
                TROVIS_CONF_HOST: host,
                TROVIS_CONF_PORT: port,
                CONF_FRAMER: FRAMER_RTU,
            }

        # Do not pass unknown serial URL schemes to the new tmodbus serial
        # backend. A real serial device path is migrated normally; anything
        # URL-like but unsupported must fail migration rather than be guessed.
        if "://" in device:
            return None

        try:
            return {
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_SERIAL,
                TROVIS_CONF_DEVICE: device,
                CONF_BAUDRATE: int(legacy_data[CONF_BAUDRATE]),
                CONF_PARITY: str(legacy_data[CONF_PARITY]),
                CONF_STOPBITS: int(legacy_data[CONF_STOPBITS]),
                CONF_BYTESIZE: int(legacy_data[CONF_BYTESIZE]),
                CONF_FRAMER: FRAMER_RTU,
            }
        except (KeyError, TypeError, ValueError):
            return None

    return None


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Migrate a TROVIS config entry to the current schema."""
    if entry.version == _TARGET_VERSION:
        return True

    if entry.version != 1:
        _LOGGER.error(
            "Cannot migrate TROVIS config entry %s from unsupported version %s",
            entry.entry_id,
            entry.version,
        )
        return False

    new_data = dict(entry.data)

    legacy_connection_entry_id = new_data.pop(
        _LEGACY_CONNECTION_ENTRY_ID,
        None,
    )

    if legacy_connection_entry_id is not None:
        legacy_entry = _legacy_connection_entry(
            hass,
            str(legacy_connection_entry_id),
        )
        if legacy_entry is None:
            _LOGGER.error(
                "Cannot migrate TROVIS config entry %s: referenced legacy "
                "Modbus Connection entry %s was not found",
                entry.entry_id,
                legacy_connection_entry_id,
            )
            return False

        migrated_connection_data = _migrate_legacy_connection_data(
            dict(legacy_entry.data)
        )
        if migrated_connection_data is None:
            _LOGGER.error(
                "Cannot migrate TROVIS config entry %s: legacy Modbus "
                "Connection entry %s contains unsupported or incomplete data",
                entry.entry_id,
                legacy_connection_entry_id,
            )
            return False

        new_data.update(migrated_connection_data)

    elif CONF_CONNECTION_TYPE not in new_data:
        _LOGGER.error(
            "Cannot migrate TROVIS config entry %s: neither legacy connection "
            "reference nor current connection data is available",
            entry.entry_id,
        )
        return False

    hass.config_entries.async_update_entry(
        entry,
        data=new_data,
        version=_TARGET_VERSION,
    )

    _LOGGER.debug(
        "Migrated TROVIS config entry %s to version %s",
        entry.entry_id,
        _TARGET_VERSION,
    )
    return True
