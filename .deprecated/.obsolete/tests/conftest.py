"""Fixtures for TROVIS tests over an in-memory owned Modbus connection."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import pytest
from custom_components.trovis557x import connection as connection_module
from modbus_connection import ModbusSerialParams, ModbusTcpParams
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

UNIT_ID: Final = 247

type TestModbusParams = ModbusTcpParams | ModbusSerialParams


# Raw Modbus protocol addresses, not manufacturer HR/CL reference numbers.
HOLDING: dict[int, int] = {
    0: 5579,  # controller model
    1: 21,  # hydraulic system / Anlage -> 2.1
    2: 305,  # firmware -> 3.05
    3: 110,  # hardware -> 1.10
    4: 0,  # special functions
    5: 12345,  # serial number
    9: 123,  # AF1 outdoor temperature -> 12.3 °C
    12: 300,  # VF1 flow temperature -> 30.0 °C
    19: 200,  # RF1 room temperature -> 20.0 °C
    22: 450,  # SF1 storage temperature -> 45.0 °C
    23: 0x7FFF,  # SF2 invalid-value marker
    24: 650,  # SF3 storage temperature -> 65.0 °C
    25: 952,  # AE1/FG1 -> 95.2
    26: 3250,  # AE2/FG2 -> 325.0
    27: 15,  # AE3/FG3 -> 1.5
    28: 120,  # pulse rate -> 120 Imp/h
    41: 523,  # analog input -> 5.23 V
    42: 175,  # summer outdoor-temperature average -> 17.5 °C
    98: 900,  # maximum flow setpoint -> 90.0 °C
    99: 1430,  # controller time -> 14:30
    100: 2106,  # controller date -> 21.06
    101: 2026,  # controller year
    102: 1,  # upper rotary switch -> automatic
    105: 1,  # Hk1 operation mode -> automatic
    106: 42,  # Hk1 valve setpoint -> 42 %
    112: 1505,  # summer operation start -> 15.05
    113: 1509,  # summer operation end -> 15.09
    114: 2,  # summer activation days
    115: 3,  # summer deactivation days
    116: 180,  # summer outdoor-temperature limit -> 18.0 °C
    117: 25,  # outdoor-temperature delay -> 2.5 K/h
    120: 20,  # temperature monitoring deviation -> 2.0 K
    121: 30,  # temperature monitoring window -> 30 min
    122: 0xFFE2,  # frost limit -> -3.0 °C
    123: 0xFE0C,  # outdoor-temperature input range start -> -50.0 °C
    124: 500,  # outdoor-temperature input range end -> 50.0 °C
    142: 246,  # station address
    153: 4,  # error count
    149: 0,  # no controller error
    999: 550,  # Hk1 flow setpoint -> 55.0 °C
    1000: 800,  # Hk1 maximum flow temperature -> 80.0 °C
    1001: 200,  # Hk1 minimum flow temperature -> 20.0 °C
    1002: 210,  # Hk1 room setpoint day -> 21.0 °C
    1003: 180,  # Hk1 room setpoint night -> 18.0 °C
    1004: 210,  # Hk1 active room setpoint -> 21.0 °C
    1005: 12,  # Hk1 gradient -> 1.2
    1006: 0,  # Hk1 level -> 0.0 K
    1008: 5,  # Hk1 return gradient -> 0.5
    1009: 20,  # Hk1 return level -> 2.0 K
    1010: 550,  # Hk1 maximum return temperature -> 55.0 °C
    1011: 300,  # Hk1 return base point -> 30.0 °C
    1012: 0xFF6A,  # Hk1 4P outdoor P1 -> -15.0 °C
    1013: 0xFFCE,  # Hk1 4P outdoor P2 -> -5.0 °C
    1014: 50,  # Hk1 4P outdoor P3 -> 5.0 °C
    1015: 150,  # Hk1 4P outdoor P4 -> 15.0 °C
    1016: 700,  # Hk1 4P flow day P1 -> 70.0 °C
    1017: 550,  # Hk1 4P flow day P2 -> 55.0 °C
    1018: 400,  # Hk1 4P flow day P3 -> 40.0 °C
    1019: 250,  # Hk1 4P flow day P4 -> 25.0 °C
    1020: 600,  # Hk1 4P flow night P1 -> 60.0 °C
    1021: 400,  # Hk1 4P flow night P2 -> 40.0 °C
    1022: 200,  # Hk1 4P flow night P3 -> 20.0 °C
    1023: 200,  # Hk1 4P flow night P4 -> 20.0 °C
    1024: 650,  # Hk1 4P return P1 -> 65.0 °C
    1025: 650,  # Hk1 4P return P2 -> 65.0 °C
    1026: 650,  # Hk1 4P return P3 -> 65.0 °C
    1027: 650,  # Hk1 4P return P4 -> 65.0 °C
    1032: 450,  # Hk1 return setpoint -> 45.0 °C
    1041: 600,  # Hk1 fixed setpoint day -> 60.0 °C
    1042: 500,  # Hk1 fixed setpoint night -> 50.0 °C
    1062: 0xFFF1,  # Hk1 flow deviation -> -1.5 K
    1099: 0,  # minimum buffer charging setpoint -> AUTO
    1100: 0,  # end buffer charging temperature -> AUTO
    1101: 60,  # buffer charging temperature boost -> 6.0 K
    1102: 10,  # buffer charging pump lag factor -> 1.0
    1103: 4,  # buffer tank status -> charging
    1199: 480,  # Hk2 flow setpoint -> 48.0 °C
    1799: 500,  # domestic hot-water setpoint -> 50.0 °C
    1800: 600,  # domestic hot-water maximum -> 60.0 °C
    1801: 450,  # domestic hot-water minimum -> 45.0 °C
    1802: 50,  # domestic hot-water hysteresis -> 5.0 K
    1803: 100,  # domestic hot-water charging temperature boost -> 10.0 K
    1804: 15,  # storage-tank-charging-pump overrun factor -> 1.5
    1805: 750,  # maximum charge temperature -> 75.0 °C
    1807: 500,  # active domestic hot-water setpoint -> 50.0 °C
    1808: 600,  # special domestic hot-water setpoint -> 60.0 °C
    1809: 100,  # solar pump-on temperature difference -> 10.0 K
    1810: 30,  # solar pump-off temperature difference -> 3.0 K
    1811: 800,  # maximum solar storage temperature -> 80.0 °C
    1812: 1234,  # solar operating hours
    1826: 4,  # storage status -> charging
    1827: 550,  # domestic hot-water maximum return -> 55.0 °C
    1829: 700,  # disinfection temperature -> 70.0 °C
    1830: 3,  # disinfection weekday -> Wednesday
    1831: 1900,  # disinfection start -> 19:00
    1832: 2100,  # disinfection end -> 21:00
    1837: 670,  # active charging set point -> 67.0 °C
    1838: 20,  # disinfection hold time -> 20 min
    1862: 0xFFF6,  # domestic hot-water control deviation -> -1.0 K
}

COILS: dict[int, bool] = {
    1: True,  # data entry active
    2: True,  # data entry performed
    3: True,  # controller initially operates autonomously
    4: False,  # Hk1 manual operation
    61: False,  # Hk1 valve closing
    62: True,  # Hk1 valve opening
    87: True,  # outdoor-temperature control autonomous
    88: True,  # Hk1 mode control autonomous
    89: True,  # Hk1 valve control autonomous
    95: True,  # Hk1 pump control autonomous
    115: True,  # Hk1 flow-setpoint control autonomous
    116: True,  # Hk1 return-setpoint control autonomous
    121: True,  # Hk1 room-setpoint control autonomous
    149: False,  # manual-operation levels not locked
    150: False,  # rotary switches not locked
    158: False,  # supervisory-system timeout inactive
    413: True,  # CL414 / CO4 -> F14 / thermal disinfection enabled
    56: True,  # Hk1 pump running
    59: True,  # domestic hot-water storage tank charging pump running
    7: False,  # domestic hot-water manual operation
    94: True,  # domestic hot-water mode control autonomous
    98: True,  # storage-tank-charging-pump control autonomous
    99: True,  # circulation-pump control autonomous
    111: True,  # special-setpoint control autonomous
    999: True,  # Hk1 automatic mode
    1000: True,  # Hk1 day mode active
    1799: True,  # domestic hot water automatic mode
    1801: True,  # domestic hot-water priority
    1802: False,  # maximum charging-temperature limit inactive
    1803: False,  # return-temperature limit inactive
    1806: False,  # forced charging inactive
    1807: True,  # solar circuit pump running
    1808: False,  # forced charging uses storage tank sensor 1
    1809: True,  # storage tank charging active
    1810: True,  # storage tank charging enabled
    1811: False,  # storage tank charging not locked
    1025: True,  # CL1026 / CO1 -> F02: Rk1 outdoor sensor enabled
    1034: False,  # CL1035 / CO1 -> F11: Rk1 gradient characteristic
    1234: False,  # CL1235 / CO2 -> F11: Rk2 gradient characteristic
    1434: False,  # CL1435 / CO3 -> F11: Rk3 gradient characteristic
}


@dataclass
class MockProvider:
    """Create TROVIS-owned mock connections while keeping a mutable test unit."""

    connection: MockModbusConnection
    unit: MockModbusUnit
    params: list[TestModbusParams] = field(default_factory=list)
    connections: list[MockModbusConnection] = field(default_factory=list)
    request_error: Exception | None = None

    def create_connection(self, params: TestModbusParams) -> MockModbusConnection:
        """Create a fresh connection using the current unit as the data template."""
        source_unit = self.unit
        connection = MockModbusConnection()
        unit = connection.for_unit(UNIT_ID)
        unit.holding.update(source_unit.holding)
        unit.input.update(source_unit.input)
        unit.coils.update(source_unit.coils)
        unit.discrete_inputs.update(source_unit.discrete_inputs)

        if self.request_error is not None:
            unit.fail_requests(self.request_error)

        self.connection = connection
        self.unit = unit
        self.params.append(params)
        self.connections.append(connection)
        return connection


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):  # noqa: ANN001
    """Allow loading the custom TROVIS integration."""
    yield


@pytest.fixture
def modbus_provider(monkeypatch: pytest.MonkeyPatch) -> MockProvider:
    """Provide a TROVIS-shaped unit behind integration-owned mock connections."""
    seed_connection = MockModbusConnection()
    seed_unit = seed_connection.for_unit(UNIT_ID)
    seed_unit.holding.update(HOLDING)
    seed_unit.coils.update(COILS)

    provider = MockProvider(
        connection=seed_connection,
        unit=seed_unit,
    )
    monkeypatch.setattr(
        connection_module,
        "ModbusConnection",
        provider.create_connection,
    )
    return provider
