"""Config flow for Trovis 557x."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SerialPortSelector,
    TextSelector,
)
from homeassistant.util import slugify
from modbus_connection import ModbusError
from trovis_modbus import DEFAULT_WRITE_ACCESS_CODE, Trovis557x

from . import create_modbus_params, with_read_retries
from .const import (
    CONF_ACCESS_CODE,
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_CONNECTION,
    CONF_CONNECTION_TYPE,
    CONF_DETECTED_SENSORS,
    CONF_DEVICE,
    CONF_FRAMER,
    CONF_HOST,
    CONF_MODEL,
    CONF_PARITY,
    CONF_PORT,
    CONF_SLUG,
    CONF_STOPBITS,
    CONF_UNIT_ID,
    CONNECTION_TYPE_SERIAL,
    CONNECTION_TYPE_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_SLUG,
    DEFAULT_STOPBITS,
    DEFAULT_UNIT_ID,
    DOMAIN,
    FRAMER_RTU,
    FRAMER_SOCKET,
    SERIAL_BAUDRATES,
)

_UNIT = NumberSelector(
    NumberSelectorConfig(
        min=1,
        max=247,
        step=1,
        mode=NumberSelectorMode.BOX,
    )
)
_ACCESS_CODE = NumberSelector(
    NumberSelectorConfig(
        min=0,
        max=9999,
        step=1,
        mode=NumberSelectorMode.BOX,
    )
)
_BAUDRATE = SelectSelector(
    SelectSelectorConfig(
        options=[str(baudrate) for baudrate in SERIAL_BAUDRATES],
        mode=SelectSelectorMode.DROPDOWN,
    )
)


def _connection_schema() -> vol.Schema:
    """Return the unified connection schema."""
    return vol.Schema(
        {
            vol.Required(CONF_CONNECTION): SerialPortSelector(),
            vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): _UNIT,
            vol.Required(
                CONF_BAUDRATE,
                default=str(DEFAULT_BAUDRATE),
            ): _BAUDRATE,
        }
    )


def _reconfigure_schema() -> vol.Schema:
    """Return the unified reconfigure schema."""
    return vol.Schema(
        {
            vol.Required(CONF_CONNECTION): SerialPortSelector(),
            vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): _UNIT,
            vol.Required(
                CONF_BAUDRATE,
                default=str(DEFAULT_BAUDRATE),
            ): _BAUDRATE,
            vol.Required(CONF_NAME): TextSelector(),
            vol.Required(CONF_ACCESS_CODE): _ACCESS_CODE,
        }
    )


def _normalize_slug(value: object) -> str:
    """Return a Home Assistant friendly entity prefix."""
    slug = slugify(str(value or ""))
    return re.sub(r"_+", "_", slug).strip("_") or DEFAULT_SLUG


def _normalize_name(value: object, fallback: str) -> str:
    """Return a non-empty display name."""
    name = str(value or "").strip()
    return name or fallback


def _device_schema(default_name: str, default_slug: str) -> vol.Schema:
    """Return the device setup schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=default_name,
            ): TextSelector(),
            vol.Required(
                CONF_SLUG,
                default=default_slug,
            ): TextSelector(),
            vol.Required(
                CONF_ACCESS_CODE,
                default=DEFAULT_WRITE_ACCESS_CODE,
            ): _ACCESS_CODE,
        }
    )


def _parse_host_port(value: str) -> tuple[str, int]:
    """Parse a host:port target, including bracketed IPv6 addresses."""
    parsed = urlsplit(f"//{value}")
    if (
        parsed.hostname is None
        or parsed.port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Invalid host:port target")

    return parsed.hostname, parsed.port


def _parse_manual_connection(value: str, unit_id: int) -> dict[str, Any]:
    """Translate one user-facing connection string to Modbus parameters."""
    normalized = value.strip()
    lowered = normalized.lower()

    if lowered.startswith("/dev/") or lowered.startswith(
        ("esphome://", "esphome-hass://")
    ):
        return {
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_SERIAL,
            CONF_DEVICE: normalized,
            CONF_UNIT_ID: unit_id,
        }

    if lowered.startswith("socket://"):
        parsed = urlsplit(normalized)
        if (
            parsed.scheme.lower() != "socket"
            or parsed.hostname is None
            or parsed.port is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Invalid socket target")

        return {
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_SERIAL,
            CONF_DEVICE: (
                f"socket://{_format_host_port(parsed.hostname, parsed.port)}"
            ),
            CONF_UNIT_ID: unit_id,
        }

    if "://" in normalized:
        raise ValueError("Unsupported connection scheme")

    host, port = _parse_host_port(normalized)
    return {
        CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP,
        CONF_HOST: host,
        CONF_PORT: port,
        CONF_UNIT_ID: unit_id,
    }


def _connection_data(user_input: dict[str, Any]) -> dict[str, Any] | None:
    """Build connection data from the unified connection form."""
    target = str(user_input.get(CONF_CONNECTION) or "").strip()
    if not target:
        return None

    baudrate = int(user_input[CONF_BAUDRATE])
    if baudrate not in SERIAL_BAUDRATES:
        raise ValueError("Unsupported TROVIS baud rate")

    data = _parse_manual_connection(
        target,
        int(user_input[CONF_UNIT_ID]),
    )

    if data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SERIAL:
        return _complete_serial_data(data, baudrate)

    # Keep the baud rate in every config entry for one uniform setup contract.
    # Native Modbus/TCP does not use it.
    return {
        **data,
        CONF_BAUDRATE: baudrate,
    }


def _complete_serial_data(data: dict[str, Any], baudrate: int) -> dict[str, Any]:
    """Apply TROVIS' fixed serial format and selected line speed."""
    return {
        **data,
        CONF_BAUDRATE: baudrate,
        CONF_PARITY: DEFAULT_PARITY,
        CONF_STOPBITS: DEFAULT_STOPBITS,
        CONF_BYTESIZE: DEFAULT_BYTESIZE,
    }


def _format_host_port(host: str, port: int) -> str:
    """Return host:port with brackets around an IPv6 literal."""
    formatted_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    return f"{formatted_host}:{port}"


def _format_connection(data: dict[str, Any]) -> str:
    """Return the user-facing connection string for stored connection data."""
    connection_type = str(data.get(CONF_CONNECTION_TYPE, ""))
    if connection_type == CONNECTION_TYPE_SERIAL:
        return str(data.get(CONF_DEVICE, ""))

    if connection_type == CONNECTION_TYPE_TCP:
        host = str(data.get(CONF_HOST, ""))
        port = int(data.get(CONF_PORT, 0))
        if not host or not port:
            return ""
        target = _format_host_port(host, port)
        if str(data.get(CONF_FRAMER, FRAMER_SOCKET)) == FRAMER_RTU:
            return f"socket://{target}"
        return target

    return ""


async def _async_probe(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> tuple[int, tuple[str, ...]] | None:
    """Probe a controller through a temporary Home Assistant Modbus unit."""
    try:
        params = create_modbus_params(data)
        async with async_get_temporary_unit(
            hass,
            params,
            int(data[CONF_UNIT_ID]),
        ) as unit:
            probe = await Trovis557x.async_probe(
                with_read_retries(unit, "TROVIS probe")
            )
    except (HomeAssistantError, ModbusError, OSError, ValueError):
        return None

    return probe.model, probe.detected_sensors


class TrovisConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Trovis 557x."""

    VERSION = 2

    _pending_data: dict[str, Any] | None = None
    _detected_model: int | None = None
    _detected_sensors: tuple[str, ...] = ()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select or enter a connection and probe the controller."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                data = _connection_data(user_input)
            except (KeyError, TypeError, ValueError):
                errors[CONF_CONNECTION] = "invalid_connection"
            else:
                if data is None:
                    errors[CONF_CONNECTION] = "connection_required"
                else:
                    probe = await _async_probe(self.hass, data)
                    if probe is None:
                        errors["base"] = "cannot_connect"
                    else:
                        self._store_probe(data, probe)
                        return await self.async_step_device()

        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(),
            errors=errors,
        )

    def _store_probe(
        self,
        data: dict[str, Any],
        probe: tuple[int, tuple[str, ...]],
    ) -> None:
        """Store a successful probe for the following flow step."""
        model, detected_sensors = probe
        self._pending_data = data
        self._detected_model = model
        self._detected_sensors = detected_sensors

    async def async_step_device(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Configure device name, entity prefix and access code."""
        if self._pending_data is None or self._detected_model is None:
            return await self.async_step_user()

        default_name = f"Trovis {self._detected_model}"
        default_slug = _normalize_slug(default_name)

        if user_input is not None:
            name = _normalize_name(
                user_input.get(CONF_NAME),
                default_name,
            )
            slug = _normalize_slug(user_input.get(CONF_SLUG) or name)
            data = {
                **self._pending_data,
                CONF_NAME: name,
                CONF_SLUG: slug,
                CONF_ACCESS_CODE: int(
                    user_input.get(
                        CONF_ACCESS_CODE,
                        DEFAULT_WRITE_ACCESS_CODE,
                    )
                ),
                CONF_MODEL: self._detected_model,
                CONF_DETECTED_SENSORS: list(self._detected_sensors),
            }
            return self.async_create_entry(
                title=name,
                data=data,
            )

        return self.async_show_form(
            step_id="device",
            data_schema=_device_schema(
                default_name,
                default_slug,
            ),
            errors={},
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Reconfigure a controller using the unified connection form."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                probe_data = _connection_data(user_input)
            except (KeyError, TypeError, ValueError):
                errors[CONF_CONNECTION] = "invalid_connection"
            else:
                if probe_data is None:
                    errors[CONF_CONNECTION] = "connection_required"
                else:
                    name = _normalize_name(
                        user_input.get(CONF_NAME),
                        entry.title,
                    )
                    access_code = int(
                        user_input.get(
                            CONF_ACCESS_CODE,
                            DEFAULT_WRITE_ACCESS_CODE,
                        )
                    )

                    probe = await _async_probe(self.hass, probe_data)
                    if probe is None:
                        errors["base"] = "cannot_connect"
                    else:
                        return self._finish_reconfigure(
                            entry,
                            probe_data,
                            name,
                            access_code,
                            probe,
                        )

        suggested_values = {
            CONF_CONNECTION: _format_connection(entry.data),
            CONF_UNIT_ID: entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID),
            CONF_BAUDRATE: str(entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)),
            CONF_NAME: entry.data.get(CONF_NAME, entry.title),
            CONF_ACCESS_CODE: entry.data.get(
                CONF_ACCESS_CODE,
                DEFAULT_WRITE_ACCESS_CODE,
            ),
        }
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _reconfigure_schema(),
                suggested_values,
            ),
            errors=errors,
        )

    def _finish_reconfigure(
        self,
        entry,
        probe_data: dict[str, Any],
        name: str,
        access_code: int,
        probe: tuple[int, tuple[str, ...]],
    ) -> ConfigFlowResult:
        """Apply a successful reconfiguration while retaining known sensors."""
        model, detected_sensors = probe
        known_sensors = set(
            entry.data.get(
                CONF_DETECTED_SENSORS,
                (),
            )
        )
        known_sensors.update(
            entry.options.get(
                CONF_DETECTED_SENSORS,
                (),
            )
        )
        known_sensors.update(detected_sensors)

        # Reconfiguration can switch transports. Replace the complete transport
        # block instead of merging it so stale TCP keys do not survive a switch
        # to serial and stale serial keys do not survive a switch to TCP.
        connection_keys = {
            CONF_CONNECTION_TYPE,
            CONF_HOST,
            CONF_PORT,
            CONF_FRAMER,
            CONF_DEVICE,
            CONF_BAUDRATE,
            CONF_PARITY,
            CONF_STOPBITS,
            CONF_BYTESIZE,
            CONF_UNIT_ID,
        }
        data = {
            key: value
            for key, value in entry.data.items()
            if key not in connection_keys
        }
        data.update(probe_data)
        data.update(
            {
                CONF_NAME: name,
                CONF_ACCESS_CODE: access_code,
                CONF_MODEL: model,
                CONF_DETECTED_SENSORS: sorted(known_sensors),
            }
        )

        return self.async_update_reload_and_abort(
            entry,
            title=name,
            data=data,
            options={},
        )
