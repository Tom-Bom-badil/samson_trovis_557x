"""Register catalog for SAMSON TROVIS."""

from __future__ import annotations

from .areas import (
    AREA_DIAGNOSTIC,
    AREA_CONTROLLER,
    AREA_HC1,
    AREA_HC2,
    AREA_HC3,
    AREA_HC4_DHW,
    AREA_MEASUREMENTS,
    AREA_MISC,
    AREA_SCHEDULES,
    AREA_HEAT_METERS,
)
from .descriptions import TrovisRegisterDescription


DIAGNOSTIC_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
MEASUREMENT_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
HC1_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
HC2_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
HC3_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
HC4_DHW_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
HEAT_METERS_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
SCHEDULE_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
MISC_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()


CONTROLLER_REGISTERS: tuple[TrovisRegisterDescription, ...] = (
    TrovisRegisterDescription(key="model", area=AREA_CONTROLLER, address=0, read_only=True, description="Controller model"),
    TrovisRegisterDescription(key="hydraulic_scheme", area=AREA_CONTROLLER, address=1, read_only=True, scale=0.1, format_as_text=True, text_decimals=1, description="Hydraulic scheme"),
    TrovisRegisterDescription(key="firmware_version", area=AREA_CONTROLLER, address=2, read_only=True, scale=0.01, format_as_text=True, text_decimals=2, description="Firmware version"),
)


REGISTER_GROUPS: dict[str, tuple[TrovisRegisterDescription, ...]] = {
    AREA_DIAGNOSTIC: DIAGNOSTIC_REGISTERS,
    AREA_CONTROLLER: CONTROLLER_REGISTERS,
    AREA_MEASUREMENTS: MEASUREMENT_REGISTERS,
    AREA_HC1: HC1_REGISTERS,
    AREA_HC2: HC2_REGISTERS,
    AREA_HC3: HC3_REGISTERS,
    AREA_HC4_DHW: HC4_DHW_REGISTERS,
    AREA_HEAT_METERS: HEAT_METERS_REGISTERS,
    AREA_SCHEDULES: SCHEDULE_REGISTERS,
    AREA_MISC: MISC_REGISTERS,
}


ALL_REGISTERS: tuple[TrovisRegisterDescription, ...] = tuple(
    register
    for group in REGISTER_GROUPS.values()
    for register in group
)



