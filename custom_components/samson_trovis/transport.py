"""Transport layer for SAMSON TROVIS.

This is the only module that should know how the Modbus backend is used.
No entity, coordinator or catalog code should import a concrete Modbus
backend directly.
"""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from modbus_connection import (
    ModbusConnection,
    ModbusConnectionError,
    ModbusError,
    ModbusExceptionError,
    ModbusTimeoutError,
    ModbusUnit,
)

from .constants.config import (
    CONF_PORT_URL,
    CONF_SLAVE_ID,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_SLAVE_ID,
    DEFAULT_STOPBITS,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


MODBUS_BACKEND_PYMODBUS = "pymodbus"
MODBUS_BACKEND_TMODBUS = "tmodbus"

# Simple spike switch:
MODBUS_BACKEND = MODBUS_BACKEND_PYMODBUS
# MODBUS_BACKEND = MODBUS_BACKEND_PYMODBUS


class TrovisTransport:
    """Thin wrapper around the selected Modbus backend."""

    def __init__(self, hass: HomeAssistant, config: ConfigEntry | Mapping[str, Any]) -> None:
        """Initialize the transport."""
        self.hass = hass

        data = config.data if isinstance(config, ConfigEntry) else config

        self.port_url = str(data[CONF_PORT_URL])
        self.slave_id = int(data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID))

        self._connection: ModbusConnection | None = None
        self._unit: ModbusUnit | None = None

    async def async_close(self) -> None:
        """Close the transport connection."""
        if self._connection is None:
            self._unit = None
            return

        try:
            await self._connection.close()
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "Error while closing TROVIS Modbus connection: port=%s slave_id=%s error=%s",
                self.port_url,
                self.slave_id,
                err,
            )
        finally:
            self._connection = None
            self._unit = None

    def _get_backend_connectors(self) -> tuple[Any, Any]:
        """Return connect functions for the selected Modbus backend."""
        if MODBUS_BACKEND == MODBUS_BACKEND_TMODBUS:
            from modbus_connection.tmodbus import connect_serial, connect_tcp

            return connect_tcp, connect_serial

        if MODBUS_BACKEND == MODBUS_BACKEND_PYMODBUS:
            from modbus_connection.pymodbus import connect_serial, connect_tcp

            return connect_tcp, connect_serial

        raise RuntimeError(f"Unsupported Modbus backend: {MODBUS_BACKEND}")

    async def _async_ensure_connected(self) -> ModbusUnit | None:
        """Ensure that a Modbus connection exists and return the unit handle."""
        if (
            self._connection is not None
            and self._unit is not None
            and self._connection.connected
        ):
            return self._unit

        await self.async_close()

        try:
            self._connection = await self._async_connect()
            self._unit = self._connection.for_unit(self.slave_id)
        except ModbusConnectionError as err:
            _LOGGER.warning(
                "Could not connect to TROVIS: backend=%s port=%s slave_id=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                err,
            )
            self._connection = None
            self._unit = None
            return None
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Unexpected error while connecting to TROVIS: backend=%s port=%s slave_id=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                err,
            )
            self._connection = None
            self._unit = None
            return None

        return self._unit

    async def _async_connect(self) -> ModbusConnection:
        """Open the Modbus connection."""
        if self.port_url.startswith("socket://"):
            parsed = urlparse(self.port_url)

            if parsed.hostname is None:
                raise ModbusConnectionError(f"Invalid socket URL: {self.port_url}")

            port = parsed.port or 502

            _LOGGER.debug(
                "Connecting TROVIS via %s / RTU-over-TCP: host=%s port=%s slave_id=%s",
                MODBUS_BACKEND,
                parsed.hostname,
                port,
                self.slave_id,
            )

            return await self._async_connect_tcp(parsed.hostname, port)

        _LOGGER.debug(
            "Connecting TROVIS via %s / serial RTU: port=%s slave_id=%s baudrate=%s parity=%s",
            MODBUS_BACKEND,
            self.port_url,
            self.slave_id,
            DEFAULT_BAUDRATE,
            DEFAULT_PARITY,
        )

        return await self._async_connect_serial()

    async def _async_connect_tcp(self, host: str, port: int) -> ModbusConnection:
        """Open TCP connection using the selected backend."""
        connect_tcp, _connect_serial = self._get_backend_connectors()

        if MODBUS_BACKEND == MODBUS_BACKEND_TMODBUS:
            return await connect_tcp(
                host,
                port=port,
                timeout=DEFAULT_TIMEOUT,
                unit_id=self.slave_id,
                framer="rtu",
            )

        return await connect_tcp(
            host,
            port=port,
            timeout=DEFAULT_TIMEOUT,
            name="samson_trovis",
            framer="rtu",
        )

    async def _async_connect_serial(self) -> ModbusConnection:
        """Open serial connection using the selected backend."""
        _connect_tcp, connect_serial = self._get_backend_connectors()

        if MODBUS_BACKEND == MODBUS_BACKEND_TMODBUS:
            return await connect_serial(
                self.port_url,
                baudrate=DEFAULT_BAUDRATE,
                bytesize=DEFAULT_BYTESIZE,
                parity=DEFAULT_PARITY,
                stopbits=DEFAULT_STOPBITS,
                unit_id=self.slave_id,
            )

        return await connect_serial(
            self.port_url,
            baudrate=DEFAULT_BAUDRATE,
            bytesize=DEFAULT_BYTESIZE,
            parity=DEFAULT_PARITY,
            stopbits=DEFAULT_STOPBITS,
            timeout=DEFAULT_TIMEOUT,
            name="samson_trovis",
        )

    async def async_read_registers(self, address: int, count: int) -> list[int] | None:
        """Read a holding register block."""
        unit = await self._async_ensure_connected()

        if unit is None:
            return None

        try:
            _LOGGER.debug(
                "Reading TROVIS holding registers: backend=%s port=%s slave_id=%s address=%s count=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
            )
            registers = await unit.read_holding_registers(address, count)
        except ModbusExceptionError as err:
            _LOGGER.warning(
                "TROVIS Modbus exception response: backend=%s port=%s slave_id=%s address=%s count=%s code=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
                err.exception_code,
            )
            return None
        except ModbusTimeoutError as err:
            _LOGGER.warning(
                "TROVIS Modbus timeout: backend=%s port=%s slave_id=%s address=%s count=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
                err,
            )
            await self.async_close()
            return None
        except ModbusError as err:
            _LOGGER.warning(
                "Failed to read TROVIS registers: backend=%s port=%s slave_id=%s address=%s count=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
                err,
            )
            await self.async_close()
            return None

        if len(registers) < count:
            _LOGGER.warning(
                "Invalid TROVIS register response: backend=%s port=%s slave_id=%s address=%s count=%s response=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
                registers,
            )
            return None

        return [int(value) for value in registers[:count]]

    async def async_read_coils(self, address: int, count: int) -> list[bool] | None:
        """Read a coil block."""
        unit = await self._async_ensure_connected()

        if unit is None:
            return None

        try:
            _LOGGER.debug(
                "Reading TROVIS coils: backend=%s port=%s slave_id=%s address=%s count=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
            )
            coils = await unit.read_coils(address, count)
        except ModbusExceptionError as err:
            _LOGGER.warning(
                "TROVIS Modbus exception response: backend=%s port=%s slave_id=%s address=%s count=%s code=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
                err.exception_code,
            )
            return None
        except ModbusTimeoutError as err:
            _LOGGER.warning(
                "TROVIS Modbus timeout: backend=%s port=%s slave_id=%s address=%s count=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
                err,
            )
            await self.async_close()
            return None
        except ModbusError as err:
            _LOGGER.warning(
                "Failed to read TROVIS coils: backend=%s port=%s slave_id=%s address=%s count=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
                err,
            )
            await self.async_close()
            return None

        if len(coils) < count:
            _LOGGER.warning(
                "Invalid TROVIS coil response: backend=%s port=%s slave_id=%s address=%s count=%s response=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                count,
                coils,
            )
            return None

        return [bool(value) for value in coils[:count]]

    async def async_write_register(self, address: int, value: int) -> bool:
        """Write a single holding register."""
        unit = await self._async_ensure_connected()

        if unit is None:
            return False

        try:
            _LOGGER.debug(
                "Writing TROVIS holding register: backend=%s port=%s slave_id=%s address=%s value=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                value,
            )
            await unit.write_register(address, value)
        except ModbusExceptionError as err:
            _LOGGER.warning(
                "TROVIS Modbus write exception response: backend=%s port=%s slave_id=%s address=%s value=%s code=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                value,
                err.exception_code,
            )
            return False
        except ModbusTimeoutError as err:
            _LOGGER.warning(
                "TROVIS Modbus write timeout: backend=%s port=%s slave_id=%s address=%s value=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                value,
                err,
            )
            await self.async_close()
            return False
        except ModbusError as err:
            _LOGGER.warning(
                "Failed to write TROVIS register: backend=%s port=%s slave_id=%s address=%s value=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                value,
                err,
            )
            await self.async_close()
            return False

        return True

    async def async_write_coil(self, address: int, value: bool) -> bool:
        """Write a single coil."""
        unit = await self._async_ensure_connected()

        if unit is None:
            return False

        try:
            _LOGGER.debug(
                "Writing TROVIS coil: backend=%s port=%s slave_id=%s address=%s value=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                value,
            )
            await unit.write_coil(address, value)
        except ModbusExceptionError as err:
            _LOGGER.warning(
                "TROVIS Modbus coil write exception response: backend=%s port=%s slave_id=%s address=%s value=%s code=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                value,
                err.exception_code,
            )
            return False
        except ModbusTimeoutError as err:
            _LOGGER.warning(
                "TROVIS Modbus coil write timeout: backend=%s port=%s slave_id=%s address=%s value=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                value,
                err,
            )
            await self.async_close()
            return False
        except ModbusError as err:
            _LOGGER.warning(
                "Failed to write TROVIS coil: backend=%s port=%s slave_id=%s address=%s value=%s error=%s",
                MODBUS_BACKEND,
                self.port_url,
                self.slave_id,
                address,
                value,
                err,
            )
            await self.async_close()
            return False

        return True