"""Transport layer for SAMSON TROVIS.

This is the only module that should know how Home Assistant / PyModbus is used.
No entity, coordinator or catalog code should import PyModbus directly.
"""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

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

try:
    from pymodbus.client import ModbusSerialClient
except ImportError:  # pragma: no cover - depends on HA runtime
    ModbusSerialClient = None

try:
    from pymodbus import FramerType
except ImportError:  # pragma: no cover - depends on pymodbus version
    try:
        from pymodbus.framer import FramerType
    except ImportError:
        FramerType = None

_LOGGER = logging.getLogger(__name__)


class TrovisTransport:
    """Thin wrapper around the Home Assistant supported Modbus backend."""

    def __init__(self, hass: HomeAssistant, config: ConfigEntry | Mapping[str, Any]) -> None:
        """Initialize the transport."""
        self.hass = hass

        data = config.data if isinstance(config, ConfigEntry) else config
        self.port_url = str(data[CONF_PORT_URL])
        self.slave_id = int(data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID))


    async def async_close(self) -> None:
        """Close the transport connection."""
        # The first config-flow test opens and closes the client per request.
        return


    async def async_read_registers(self, address: int, count: int) -> list[int] | None:
        """Read a holding register block."""
        return await self.hass.async_add_executor_job(
            self._read_registers_sync,
            address,
            count,
        )


    def _read_registers_sync(self, address: int, count: int) -> list[int] | None:
        """Read holding registers using the synchronous PyModbus client."""
        if ModbusSerialClient is None:
            _LOGGER.error("PyModbus is not available in the Home Assistant runtime")
            return None

        client = self._create_client()

        try:
            if not client.connect():
                _LOGGER.warning("Could not connect to TROVIS on %s", self.port_url)
                return None

            _LOGGER.debug(
                "Reading TROVIS holding registers: port=%s slave_id=%s address=%s count=%s",
                self.port_url,
                self.slave_id,
                address,
                count,
            )

            response = self._read_holding_registers(client, address, count)

            if response is None:
                return None

            if hasattr(response, "isError") and response.isError():
                _LOGGER.warning(
                    "TROVIS Modbus error response: port=%s slave_id=%s address=%s count=%s response=%s",
                    self.port_url,
                    self.slave_id,
                    address,
                    count,
                    response,
                )
                return None

            registers = getattr(response, "registers", None)
            if not isinstance(registers, list) or len(registers) < count:
                _LOGGER.warning(
                    "Invalid TROVIS register response: port=%s slave_id=%s address=%s count=%s response=%s",
                    self.port_url,
                    self.slave_id,
                    address,
                    count,
                    response,
                )
                return None

            return [int(value) for value in registers[:count]]

        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to read TROVIS registers: port=%s slave_id=%s address=%s count=%s error=%s",
                self.port_url,
                self.slave_id,
                address,
                count,
                err,
            )
            return None

        finally:
            client.close()


    def _read_coils_sync(self, address: int, count: int) -> list[bool] | None:
        """Read coils using the synchronous PyModbus client."""
        if ModbusSerialClient is None:
            _LOGGER.error("PyModbus is not available in the Home Assistant runtime")
            return None

        client = self._create_client()

        try:
            if not client.connect():
                _LOGGER.warning("Could not connect to TROVIS on %s", self.port_url)
                return None

            _LOGGER.debug(
                "Reading TROVIS coils: port=%s slave_id=%s address=%s count=%s",
                self.port_url,
                self.slave_id,
                address,
                count,
            )

            response = self._read_coils(client, address, count)

            if response is None:
                return None

            if hasattr(response, "isError") and response.isError():
                _LOGGER.warning(
                    "TROVIS Modbus error response: port=%s slave_id=%s address=%s count=%s response=%s",
                    self.port_url,
                    self.slave_id,
                    address,
                    count,
                    response,
                )
                return None

            bits = getattr(response, "bits", None)
            if not isinstance(bits, list) or len(bits) < count:
                _LOGGER.warning(
                    "Invalid TROVIS coil response: port=%s slave_id=%s address=%s count=%s response=%s",
                    self.port_url,
                    self.slave_id,
                    address,
                    count,
                    response,
                )
                return None

            return [bool(value) for value in bits[:count]]

        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to read TROVIS coils: port=%s slave_id=%s address=%s count=%s error=%s",
                self.port_url,
                self.slave_id,
                address,
                count,
                err,
            )
            return None

        finally:
            client.close()


    def _read_coils(self, client: Any, address: int, count: int) -> Any:
        """Read coils with PyModbus version compatibility."""
        for slave_kwarg in (
            {"device_id": self.slave_id},
            {"slave": self.slave_id},
            {"unit": self.slave_id},
        ):
            try:
                return client.read_coils(
                    address=address,
                    count=count,
                    **slave_kwarg,
                )
            except TypeError:
                continue

        _LOGGER.warning("Installed PyModbus version does not support known slave/device_id arguments")
        return None


    def _create_client(self) -> Any:
        """Create a PyModbus serial client.

        Newer PyModbus versions use framer=FramerType.RTU.
        Older versions used method="rtu".
        """
        kwargs = {
            "port": self.port_url,
            "baudrate": DEFAULT_BAUDRATE,
            "bytesize": DEFAULT_BYTESIZE,
            "parity": DEFAULT_PARITY,
            "stopbits": DEFAULT_STOPBITS,
            "timeout": DEFAULT_TIMEOUT,
            "retries": 1,
        }

        if FramerType is not None:
            try:
                return ModbusSerialClient(framer=FramerType.RTU, **kwargs)
            except TypeError:
                pass

        return ModbusSerialClient(method="rtu", **kwargs)


    def _read_holding_registers(self, client: Any, address: int, count: int) -> Any:
        """Read holding registers with PyModbus version compatibility."""
        for slave_kwarg in (
            {"device_id": self.slave_id},
            {"slave": self.slave_id},
            {"unit": self.slave_id},
        ):
            try:
                return client.read_holding_registers(
                    address=address,
                    count=count,
                    **slave_kwarg,
                )
            except TypeError:
                continue

        _LOGGER.warning("Installed PyModbus version does not support known slave/device_id arguments")
        return None


    async def async_read_coils(self, address: int, count: int) -> list[bool] | None:
        """Read a coil block."""
        return await self.hass.async_add_executor_job(
            self._read_coils_sync,
            address,
            count,
        )


    async def async_write_register(self, address: int, value: int) -> bool:
        """Write a single holding register."""
        return await self.hass.async_add_executor_job(
            self._write_register_sync,
            address,
            value,
        )


    def _write_register_sync(self, address: int, value: int) -> bool:
        """Write a single holding register using the synchronous PyModbus client."""
        if ModbusSerialClient is None:
            _LOGGER.error("PyModbus is not available in the Home Assistant runtime")
            return False

        client = self._create_client()

        try:
            if not client.connect():
                _LOGGER.warning("Could not connect to TROVIS on %s", self.port_url)
                return False

            _LOGGER.debug(
                "Writing TROVIS holding register: port=%s slave_id=%s address=%s value=%s",
                self.port_url,
                self.slave_id,
                address,
                value,
            )

            response = self._write_register(client, address, value)

            if response is None:
                return False

            if hasattr(response, "isError") and response.isError():
                _LOGGER.warning(
                    "TROVIS Modbus write error response: port=%s slave_id=%s address=%s value=%s response=%s",
                    self.port_url,
                    self.slave_id,
                    address,
                    value,
                    response,
                )
                return False

            return True

        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to write TROVIS register: port=%s slave_id=%s address=%s value=%s error=%s",
                self.port_url,
                self.slave_id,
                address,
                value,
                err,
            )
            return False

        finally:
            client.close()


    def _write_register(self, client: Any, address: int, value: int) -> Any:
        """Write a register with PyModbus version compatibility."""
        for slave_kwarg in (
            {"device_id": self.slave_id},
            {"slave": self.slave_id},
            {"unit": self.slave_id},
        ):
            try:
                return client.write_register(
                    address=address,
                    value=value,
                    **slave_kwarg,
                )
            except TypeError:
                continue

        _LOGGER.warning("Installed PyModbus version does not support known slave/device_id arguments")
        return None


    async def async_write_coil(self, address: int, value: bool) -> bool:
        """Write a single coil."""
        _LOGGER.debug("Write coil not implemented yet: address=%s value=%s", address, value)
        return False