"""Modbus connection helpers for the TROVIS 557x integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, cast

from modbus_connection import ModbusSerialParams, ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_CONNECTION_TYPE,
    CONF_DEVICE,
    CONF_FRAMER,
    CONF_HOST,
    CONF_PARITY,
    CONF_PORT,
    CONF_STOPBITS,
    CONNECTION_TYPE_SERIAL,
    CONNECTION_TYPE_TCP,
    FRAMER_RTU,
    FRAMER_SOCKET,
)

type TrovisModbusParams = ModbusTcpParams | ModbusSerialParams


def build_modbus_params(data: Mapping[str, Any]) -> TrovisModbusParams:
    """Build backend-neutral Modbus parameters from TROVIS config data."""
    connection_type = str(data[CONF_CONNECTION_TYPE])

    if connection_type == CONNECTION_TYPE_TCP:
        framer = cast(
            Literal["socket", "rtu"],
            str(data.get(CONF_FRAMER, FRAMER_SOCKET)),
        )
        return ModbusTcpParams(
            host=str(data[CONF_HOST]),
            port=int(data[CONF_PORT]),
            framer=framer,
        )

    if connection_type == CONNECTION_TYPE_SERIAL:
        return ModbusSerialParams(
            device=str(data[CONF_DEVICE]),
            baudrate=int(data[CONF_BAUDRATE]),
            bytesize=cast(Literal[7, 8], int(data[CONF_BYTESIZE])),
            parity=cast(Literal["N", "E", "O"], str(data[CONF_PARITY])),
            stopbits=cast(Literal[1, 2], int(data[CONF_STOPBITS])),
            framer=FRAMER_RTU,
        )

    raise ValueError(f"Unsupported Modbus connection type: {connection_type!r}")


def create_modbus_connection(data: Mapping[str, Any]) -> ModbusConnection:
    """Create the TROVIS-owned tmodbus connection without opening it."""
    return ModbusConnection(build_modbus_params(data))
