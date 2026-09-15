"""Map neutral trovis-modbus metadata to Home Assistant attributes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from trovis_modbus.metadata import (
    BooleanMetadata,
    DatapointMetadata,
    EnumMetadata,
    NumberMetadata,
)


def require_datapoint_metadata(component: Any, field: str) -> DatapointMetadata:
    """Return neutral TROVIS metadata for a component field."""
    if hasattr(component, "metadata_for"):
        metadata = component.metadata_for(field)
        if metadata is not None:
            return metadata

    if hasattr(component, "require_metadata_for"):
        try:
            return component.require_metadata_for(field)
        except (AttributeError, KeyError) as err:
            raise ValueError(f"TROVIS field {field!r} has no metadata") from err

    raise ValueError(f"TROVIS field {field!r} has no metadata")


def component_supports_datapoint(component: Any, field: str) -> bool:
    """Return whether a component exposes metadata for a datapoint."""
    try:
        require_datapoint_metadata(component, field)
    except ValueError:
        return False
    return True


def require_number_metadata(component: Any, field: str) -> NumberMetadata:
    """Return number metadata for a component field."""
    metadata = require_datapoint_metadata(component, field)
    if metadata.number is None:
        raise ValueError(f"TROVIS field {field!r} is not numeric")
    return metadata.number


def require_enum_metadata(component: Any, field: str) -> EnumMetadata:
    """Return enum metadata for a component field."""
    metadata = require_datapoint_metadata(component, field)
    if metadata.enum is None:
        raise ValueError(f"TROVIS field {field!r} is not an enum")
    return metadata.enum


def require_boolean_metadata(component: Any, field: str) -> BooleanMetadata:
    """Return boolean metadata for a component field."""
    metadata = require_datapoint_metadata(component, field)
    if metadata.boolean is None:
        raise ValueError(f"TROVIS field {field!r} is not boolean")
    return metadata.boolean


def ha_unit_from_number(number: NumberMetadata) -> str | None:
    """Map a neutral TROVIS unit to a Home Assistant unit."""
    unit = number.unit

    if unit == "°C":
        return UnitOfTemperature.CELSIUS

    if unit == "K":
        return UnitOfTemperature.KELVIN

    if unit is None or unit.strip() == "":
        return None

    return unit


def number_device_class_from_number(
    number: NumberMetadata,
) -> NumberDeviceClass | None:
    """Infer a Home Assistant number device class from neutral metadata."""
    if number.unit == "°C":
        return NumberDeviceClass.TEMPERATURE

    # Do not map "K" automatically. In TROVIS this is often a temperature
    # difference / curve offset, not an absolute temperature.
    return None


def sensor_device_class_from_number(
    number: NumberMetadata,
) -> SensorDeviceClass | None:
    """Infer a Home Assistant sensor device class from neutral metadata."""
    if number.unit == "°C":
        return SensorDeviceClass.TEMPERATURE

    if number.unit == "V":
        return SensorDeviceClass.VOLTAGE

    # As for number entities, K commonly represents a difference or offset.
    return None
