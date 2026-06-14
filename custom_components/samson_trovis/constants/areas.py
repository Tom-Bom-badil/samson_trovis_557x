"""Functional areas for SAMSON TROVIS."""

from __future__ import annotations

AREA_CONTROLLER = "controller"
AREA_MEASUREMENTS = "measurements"
AREA_HC1 = "hc1"
AREA_HC2 = "hc2"
AREA_HC3 = "hc3"
AREA_HC4_DHW = "hc4_dhw"
AREA_HEAT_METERS = "heat_meters"
AREA_SCHEDULES = "schedules"
AREA_MISC = "miscellaneous"
AREA_DIAGNOSTIC = "diagnostic"

SELECTABLE_AREAS: tuple[str, ...] = (
    AREA_CONTROLLER,
    AREA_MEASUREMENTS,
    AREA_HC1,
    AREA_HC2,
    AREA_HC3,
    AREA_HC4_DHW,
    AREA_HEAT_METERS,
    AREA_SCHEDULES,
    AREA_MISC,
    AREA_DIAGNOSTIC,
)

DEFAULT_ENABLED_AREAS: tuple[str, ...] = (
    AREA_CONTROLLER,
    AREA_MEASUREMENTS,
    AREA_HC1,
    AREA_HC2,
    AREA_HC4_DHW,
)
