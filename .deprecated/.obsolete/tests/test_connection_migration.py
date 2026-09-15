"""Tests for TROVIS connection parameters, migration and reconfiguration."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from custom_components.trovis557x.connection import build_modbus_params
from custom_components.trovis557x.const import (
    CONF_ACCESS_CODE,
    CONF_BAUDRATE,
    CONF_BYTESIZE,
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
    DOMAIN,
    FRAMER_RTU,
    FRAMER_SOCKET,
)
from custom_components.trovis557x.migration import async_migrate_entry
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.const import (
    CONF_DEVICE as LEGACY_CONF_DEVICE,
    CONF_HOST as LEGACY_CONF_HOST,
    CONF_PORT as LEGACY_CONF_PORT,
    CONF_TYPE as LEGACY_CONF_TYPE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from modbus_connection import ModbusSerialParams, ModbusTcpParams
from pytest_homeassistant_custom_component.common import MockConfigEntry
from trovis_modbus import DEFAULT_WRITE_ACCESS_CODE

from .conftest import UNIT_ID, MockProvider

LEGACY_CONNECTION_ENTRY_ID = "connection_entry_id"


def _base_device_data() -> dict[str, object]:
    """Return device-specific data that migration must preserve."""
    return {
        CONF_UNIT_ID: UNIT_ID,
        "name": "Existing TROVIS",
        CONF_SLUG: "existing_trovis",
        CONF_ACCESS_CODE: DEFAULT_WRITE_ACCESS_CODE,
        CONF_MODEL: 5579,
        CONF_DETECTED_SENSORS: ["af1", "vf1"],
    }


@pytest.mark.parametrize("framer", [FRAMER_SOCKET, FRAMER_RTU])
def test_build_tcp_params(framer: str) -> None:
    """Build native TCP and RTU-over-TCP parameter objects."""
    params = build_modbus_params(
        {
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP,
            CONF_HOST: "192.0.2.20",
            CONF_PORT: 1502,
            CONF_FRAMER: framer,
        }
    )

    assert isinstance(params, ModbusTcpParams)
    assert params.host == "192.0.2.20"
    assert params.port == 1502
    assert params.framer == framer


def test_build_serial_params() -> None:
    """Build RTU serial parameters from config-entry data."""
    params = build_modbus_params(
        {
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_SERIAL,
            CONF_DEVICE: "/dev/ttyUSB0",
            CONF_BAUDRATE: 19200,
            CONF_BYTESIZE: 8,
            CONF_PARITY: "E",
            CONF_STOPBITS: 1,
        }
    )

    assert isinstance(params, ModbusSerialParams)
    assert params.device == "/dev/ttyUSB0"
    assert params.baudrate == 19200
    assert params.bytesize == 8
    assert params.parity == "E"
    assert params.stopbits == 1
    assert params.framer == FRAMER_RTU


async def test_migrate_v1_tcp_entry(hass: HomeAssistant) -> None:
    """Copy a legacy Modbus TCP provider into the TROVIS config entry."""
    legacy_entry = MockConfigEntry(
        domain="modbus_connection",
        title="Legacy TCP",
        data={
            LEGACY_CONF_TYPE: CONNECTION_TYPE_TCP,
            LEGACY_CONF_HOST: "192.0.2.30",
            LEGACY_CONF_PORT: 502,
        },
        version=1,
    )
    legacy_entry.add_to_hass(hass)

    original = {
        **_base_device_data(),
        LEGACY_CONNECTION_ENTRY_ID: legacy_entry.entry_id,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing TROVIS",
        data=original,
        options={"unchanged_option": True},
        version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == 2
    assert LEGACY_CONNECTION_ENTRY_ID not in entry.data
    assert entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_TCP
    assert entry.data[CONF_HOST] == "192.0.2.30"
    assert entry.data[CONF_PORT] == 502
    assert entry.data[CONF_FRAMER] == FRAMER_SOCKET
    for key, value in _base_device_data().items():
        assert entry.data[key] == value
    assert dict(entry.options) == {"unchanged_option": True}


async def test_migrate_v1_serial_entry(hass: HomeAssistant) -> None:
    """Copy a legacy serial provider into the TROVIS config entry."""
    legacy_entry = MockConfigEntry(
        domain="modbus_connection",
        title="Legacy Serial",
        data={
            LEGACY_CONF_TYPE: CONNECTION_TYPE_SERIAL,
            LEGACY_CONF_DEVICE: "/dev/ttyUSB1",
            CONF_BAUDRATE: 19200,
            CONF_BYTESIZE: 8,
            CONF_PARITY: "O",
            CONF_STOPBITS: 2,
        },
        version=1,
    )
    legacy_entry.add_to_hass(hass)

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing TROVIS",
        data={
            **_base_device_data(),
            LEGACY_CONNECTION_ENTRY_ID: legacy_entry.entry_id,
        },
        version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == 2
    assert LEGACY_CONNECTION_ENTRY_ID not in entry.data
    assert entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SERIAL
    assert entry.data[CONF_DEVICE] == "/dev/ttyUSB1"
    assert entry.data[CONF_BAUDRATE] == 19200
    assert entry.data[CONF_BYTESIZE] == 8
    assert entry.data[CONF_PARITY] == "O"
    assert entry.data[CONF_STOPBITS] == 2
    assert entry.data[CONF_FRAMER] == FRAMER_RTU


async def test_migrate_v1_socket_serial_entry_to_rtu_over_tcp(
    hass: HomeAssistant,
) -> None:
    """Convert legacy socket:// serial transport to first-class RTU-over-TCP."""
    legacy_entry = MockConfigEntry(
        domain="modbus_connection",
        title="Legacy RTU over TCP",
        data={
            LEGACY_CONF_TYPE: CONNECTION_TYPE_SERIAL,
            LEGACY_CONF_DEVICE: "socket://192.168.178.59:502",
            CONF_BAUDRATE: 19200,
            CONF_BYTESIZE: 8,
            CONF_PARITY: "N",
            CONF_STOPBITS: 1,
        },
        version=1,
    )
    legacy_entry.add_to_hass(hass)

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing TROVIS",
        data={
            **_base_device_data(),
            LEGACY_CONNECTION_ENTRY_ID: legacy_entry.entry_id,
        },
        version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == 2
    assert LEGACY_CONNECTION_ENTRY_ID not in entry.data
    assert entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_TCP
    assert entry.data[CONF_HOST] == "192.168.178.59"
    assert entry.data[CONF_PORT] == 502
    assert entry.data[CONF_FRAMER] == FRAMER_RTU
    assert CONF_DEVICE not in entry.data
    assert CONF_BAUDRATE not in entry.data
    assert CONF_BYTESIZE not in entry.data
    assert CONF_PARITY not in entry.data
    assert CONF_STOPBITS not in entry.data


async def test_migration_rejects_unknown_serial_url(
    hass: HomeAssistant,
) -> None:
    """Do not guess how an unsupported serial URL should be transported."""
    legacy_entry = MockConfigEntry(
        domain="modbus_connection",
        title="Unsupported serial URL",
        data={
            LEGACY_CONF_TYPE: CONNECTION_TYPE_SERIAL,
            LEGACY_CONF_DEVICE: "rfc2217://192.0.2.90:4001",
            CONF_BAUDRATE: 19200,
            CONF_BYTESIZE: 8,
            CONF_PARITY: "N",
            CONF_STOPBITS: 1,
        },
        version=1,
    )
    legacy_entry.add_to_hass(hass)

    original = {
        **_base_device_data(),
        LEGACY_CONNECTION_ENTRY_ID: legacy_entry.entry_id,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing TROVIS",
        data=original,
        version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False
    assert entry.version == 1
    assert dict(entry.data) == original


async def test_migration_fails_when_legacy_entry_is_missing(
    hass: HomeAssistant,
) -> None:
    """Do not guess connection data if the referenced provider is gone."""
    original = {
        **_base_device_data(),
        LEGACY_CONNECTION_ENTRY_ID: "missing-entry",
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing TROVIS",
        data=original,
        version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False

    assert entry.version == 1
    assert dict(entry.data) == original


async def test_migration_fails_when_legacy_entry_is_incomplete(
    hass: HomeAssistant,
) -> None:
    """Do not partially migrate incomplete legacy connection data."""
    legacy_entry = MockConfigEntry(
        domain="modbus_connection",
        title="Broken TCP",
        data={
            LEGACY_CONF_TYPE: CONNECTION_TYPE_TCP,
            LEGACY_CONF_HOST: "192.0.2.40",
        },
        version=1,
    )
    legacy_entry.add_to_hass(hass)

    original = {
        **_base_device_data(),
        LEGACY_CONNECTION_ENTRY_ID: legacy_entry.entry_id,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing TROVIS",
        data=original,
        version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False

    assert entry.version == 1
    assert dict(entry.data) == original


async def test_reconfigure_tcp_to_serial_cleans_transport_and_keeps_sensor_union(
    hass: HomeAssistant,
    modbus_provider: MockProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Switch transports without retaining obsolete TCP credentials."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing TROVIS",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP,
            CONF_HOST: "192.0.2.50",
            CONF_PORT: 502,
            CONF_FRAMER: FRAMER_SOCKET,
            CONF_UNIT_ID: UNIT_ID,
            "name": "Existing TROVIS",
            CONF_SLUG: "existing_trovis",
            CONF_ACCESS_CODE: DEFAULT_WRITE_ACCESS_CODE,
            CONF_MODEL: 5579,
            CONF_DETECTED_SENSORS: ["historic_sensor"],
        },
        options={CONF_DETECTED_SENSORS: ["option_sensor"]},
        version=2,
    )
    entry.add_to_hass(hass)

    schedule_reload = Mock()
    monkeypatch.setattr(
        hass.config_entries,
        "async_schedule_reload",
        schedule_reload,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert result["type"] is FlowResultType.MENU
    assert set(result["menu_options"]) == {
        "reconfigure_network",
        "reconfigure_serial",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "reconfigure_serial"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure_serial"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DEVICE: "/dev/ttyUSB2",
            CONF_BAUDRATE: 19200,
            CONF_PARITY: "N",
            CONF_STOPBITS: 1,
            CONF_BYTESIZE: 8,
            CONF_UNIT_ID: UNIT_ID,
            "name": "Reconfigured TROVIS",
            CONF_ACCESS_CODE: 1732,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    schedule_reload.assert_called_once_with(entry.entry_id)

    assert entry.title == "Reconfigured TROVIS"
    assert entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SERIAL
    assert entry.data[CONF_DEVICE] == "/dev/ttyUSB2"
    assert entry.data[CONF_BAUDRATE] == 19200
    assert entry.data[CONF_SLUG] == "existing_trovis"
    assert CONF_HOST not in entry.data
    assert CONF_PORT not in entry.data
    assert CONF_FRAMER not in entry.data
    assert "historic_sensor" in entry.data[CONF_DETECTED_SENSORS]
    assert "option_sensor" in entry.data[CONF_DETECTED_SENSORS]
    assert "af1" in entry.data[CONF_DETECTED_SENSORS]
    assert dict(entry.options) == {}


async def test_reconfigure_serial_to_tcp_cleans_serial_transport(
    hass: HomeAssistant,
    modbus_provider: MockProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Switch to TCP without retaining obsolete serial settings."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing TROVIS",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_SERIAL,
            CONF_DEVICE: "/dev/ttyUSB3",
            CONF_BAUDRATE: 9600,
            CONF_PARITY: "N",
            CONF_STOPBITS: 1,
            CONF_BYTESIZE: 8,
            CONF_UNIT_ID: UNIT_ID,
            "name": "Existing TROVIS",
            CONF_SLUG: "existing_trovis",
            CONF_ACCESS_CODE: DEFAULT_WRITE_ACCESS_CODE,
            CONF_MODEL: 5579,
            CONF_DETECTED_SENSORS: ["af1"],
        },
        version=2,
    )
    entry.add_to_hass(hass)

    schedule_reload = Mock()
    monkeypatch.setattr(
        hass.config_entries,
        "async_schedule_reload",
        schedule_reload,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "reconfigure_network"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.0.2.60",
            CONF_PORT: 1502,
            CONF_FRAMER: FRAMER_RTU,
            CONF_UNIT_ID: UNIT_ID,
            "name": "Network TROVIS",
            CONF_ACCESS_CODE: DEFAULT_WRITE_ACCESS_CODE,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    schedule_reload.assert_called_once_with(entry.entry_id)

    assert entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_TCP
    assert entry.data[CONF_HOST] == "192.0.2.60"
    assert entry.data[CONF_PORT] == 1502
    assert entry.data[CONF_FRAMER] == FRAMER_RTU
    assert CONF_DEVICE not in entry.data
    assert CONF_BAUDRATE not in entry.data
    assert CONF_PARITY not in entry.data
    assert CONF_STOPBITS not in entry.data
    assert CONF_BYTESIZE not in entry.data
