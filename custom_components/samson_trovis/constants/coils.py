"""Coil catalog for SAMSON TROVIS."""

from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from .descriptions import TrovisCoilDescription
from .areas import (
    AREA_CONTROLLER,
    AREA_DIAGNOSTIC,
    AREA_MEASUREMENTS,
    AREA_HEATING_CIRCUIT_1,
    AREA_HEATING_CIRCUIT_2,
    AREA_HEATING_CIRCUIT_3,
    AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER,
    AREA_HEAT_METERS,
    AREA_MISCELLANEOUS,
    AREA_SCHEDULES,
)


DIAGNOSTIC_COILS: tuple[TrovisCoilDescription, ...] = ()
MEASUREMENT_COILS: tuple[TrovisCoilDescription, ...] = ()
HEATING_CIRCUIT_1_COILS: tuple[TrovisCoilDescription, ...] = ()
HEATING_CIRCUIT_2_COILS: tuple[TrovisCoilDescription, ...] = ()
HEATING_CIRCUIT_3_COILS: tuple[TrovisCoilDescription, ...] = ()
HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER_COILS: tuple[TrovisCoilDescription, ...] = ()
HEAT_METERS_COILS: tuple[TrovisCoilDescription, ...] = ()
SCHEDULE_COILS: tuple[TrovisCoilDescription, ...] = ()
MISCELLANEOUS_COILS: tuple[TrovisCoilDescription, ...] = ()


CONTROLLER_COILS: tuple[TrovisCoilDescription, ...] = (
    TrovisCoilDescription(key="general_fault", area=AREA_CONTROLLER, address=0, read_only=True, device_class=BinarySensorDeviceClass.PROBLEM, description="Controller general fault"),
    TrovisCoilDescription(key="manual_mode_lock", area=AREA_CONTROLLER, address=149, read_only=True, description="Manual mode lock"),
    TrovisCoilDescription(key="rotary_switch_lock", area=AREA_CONTROLLER, address=150, read_only=True, description="Rotary switch lock"),
)


COIL_GROUPS: dict[str, tuple[TrovisCoilDescription, ...]] = {
    AREA_DIAGNOSTIC: DIAGNOSTIC_COILS,
    AREA_CONTROLLER: CONTROLLER_COILS,
    AREA_MEASUREMENTS: MEASUREMENT_COILS,
    AREA_HEATING_CIRCUIT_1: HEATING_CIRCUIT_1_COILS,
    AREA_HEATING_CIRCUIT_2: HEATING_CIRCUIT_2_COILS,
    AREA_HEATING_CIRCUIT_3: HEATING_CIRCUIT_3_COILS,
    AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER: HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER_COILS,
    AREA_HEAT_METERS: HEAT_METERS_COILS,
    AREA_SCHEDULES: SCHEDULE_COILS,
    AREA_MISCELLANEOUS: MISCELLANEOUS_COILS,
}


ALL_COILS: tuple[TrovisCoilDescription, ...] = tuple(
    coil
    for group in COIL_GROUPS.values()
    for coil in group
)
