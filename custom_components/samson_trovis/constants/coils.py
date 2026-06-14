"""Coil catalog for SAMSON TROVIS."""

from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from .descriptions import TrovisCoilDescription
from .areas import (
    AREA_CONTROLLER,
    AREA_DIAGNOSTIC,
    AREA_HC1,
    AREA_HC2,
    AREA_HC3,
    AREA_HC4_DHW,
    AREA_HEAT_METERS,
    AREA_MEASUREMENTS,
    AREA_MISC,
    AREA_SCHEDULES,
)


DIAGNOSTIC_COILS: tuple[TrovisCoilDescription, ...] = ()
MEASUREMENT_COILS: tuple[TrovisCoilDescription, ...] = ()
HC1_COILS: tuple[TrovisCoilDescription, ...] = ()
HC2_COILS: tuple[TrovisCoilDescription, ...] = ()
HC3_COILS: tuple[TrovisCoilDescription, ...] = ()
HC4_DHW_COILS: tuple[TrovisCoilDescription, ...] = ()
HEAT_METERS_COILS: tuple[TrovisCoilDescription, ...] = ()
SCHEDULE_COILS: tuple[TrovisCoilDescription, ...] = ()
MISC_COILS: tuple[TrovisCoilDescription, ...] = ()

CONTROLLER_COILS: tuple[TrovisCoilDescription, ...] = (
    TrovisCoilDescription(key="general_fault", area=AREA_CONTROLLER, address=0, read_only=True, device_class=BinarySensorDeviceClass.PROBLEM, description="Controller general fault"),
    TrovisCoilDescription(key="manual_mode_lock", area=AREA_CONTROLLER, address=149, read_only=True, description="Manual mode lock"),
    TrovisCoilDescription(key="rotary_switch_lock", area=AREA_CONTROLLER, address=150, read_only=True, description="Rotary switch lock"),
)


COIL_GROUPS: dict[str, tuple[TrovisCoilDescription, ...]] = {
    AREA_DIAGNOSTIC: DIAGNOSTIC_COILS,
    AREA_CONTROLLER: CONTROLLER_COILS,
    AREA_MEASUREMENTS: MEASUREMENT_COILS,
    AREA_HC1: HC1_COILS,
    AREA_HC2: HC2_COILS,
    AREA_HC3: HC3_COILS,
    AREA_HC4_DHW: HC4_DHW_COILS,
    AREA_HEAT_METERS: HEAT_METERS_COILS,
    AREA_SCHEDULES: SCHEDULE_COILS,
    AREA_MISC: MISC_COILS,
}


ALL_COILS: tuple[TrovisCoilDescription, ...] = tuple(
    coil
    for group in COIL_GROUPS.values()
    for coil in group
)
