"""Functional areas for SAMSON TROVIS."""

from __future__ import annotations

AREA_CONTROLLER = "controller"
AREA_MEASUREMENTS = "measurements"
AREA_HEATING_CIRCUIT_1 = "heating_circuit_1"
AREA_HEATING_CIRCUIT_2 = "heating_circuit_2"
AREA_HEATING_CIRCUIT_3 = "heating_circuit_3"
AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER = "heating_circuit_4_domestic_hot_water"
AREA_HEAT_METERS = "heat_meters"
AREA_SCHEDULES = "schedules"
AREA_MISCELLANEOUS = "miscellaneous"
AREA_DIAGNOSTIC = "diagnostic"

SELECTABLE_AREAS: tuple[str, ...] = (
    AREA_CONTROLLER,
    AREA_MEASUREMENTS,
    AREA_HEATING_CIRCUIT_1,
    AREA_HEATING_CIRCUIT_2,
    AREA_HEATING_CIRCUIT_3,
    AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER,
    AREA_HEAT_METERS,
    AREA_SCHEDULES,
    AREA_MISCELLANEOUS,
    AREA_DIAGNOSTIC,
)

DEFAULT_ENABLED_AREAS: tuple[str, ...] = (
    AREA_CONTROLLER,
    AREA_MEASUREMENTS,
    AREA_HEATING_CIRCUIT_1,
    AREA_HEATING_CIRCUIT_2,  # delete for production
    AREA_HEATING_CIRCUIT_3,  # delete for production
    AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER,
)

ROOT_DEVICE_AREAS: tuple[str, ...] = (
    AREA_CONTROLLER,
    AREA_MISCELLANEOUS,
    AREA_DIAGNOSTIC,
)

AREA_DEVICE_NAMES: dict[str, str] = {
    AREA_MEASUREMENTS: "Measurements",
    AREA_HEATING_CIRCUIT_1: "Heating circuit 1",
    AREA_HEATING_CIRCUIT_2: "Heating circuit 2",
    AREA_HEATING_CIRCUIT_3: "Heating circuit 3",
    AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER: "Heating circuit 4 (Hot water)",
    AREA_HEAT_METERS: "Heat meters",
    AREA_SCHEDULES: "Schedules",
}
