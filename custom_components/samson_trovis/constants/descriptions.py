"""Description classes for SAMSON TROVIS data points."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import Platform


class TrovisEntityDescription(Protocol):
    """Common TROVIS entity description protocol."""

    key: str
    area: str
    address: int | None
    read_only: bool


class TrovisRegisterValueType(StrEnum):
    """Supported register value types."""

    UNSIGNED = "unsigned"
    SIGNED = "signed"
    ENUM = "enum"


@dataclass(frozen=True, kw_only=True)
class TrovisRegisterDescription(SensorEntityDescription):
    """Description of one TROVIS register."""

    area: str
    address: int | None = None
    read_only: bool = True
    platform: Platform = Platform.SENSOR
    name: str | None = None
    value_type: TrovisRegisterValueType = TrovisRegisterValueType.UNSIGNED
    scale: float = 1.0
    offset: float = 0.0
    native_min_value: float | None = None
    native_max_value: float | None = None
    native_step: float | None = None
    enum_map: dict[int, str] | None = None
    invalid_values: tuple[int, ...] = (32767,)
    description: str | None = None
    format_as_text: bool = False
    text_decimals: int | None = None


@dataclass(frozen=True, kw_only=True)
class TrovisCoilDescription(BinarySensorEntityDescription):
    """Description of one TROVIS coil."""

    area: str
    address: int | None = None
    read_only: bool = True
    platform: Platform = Platform.BINARY_SENSOR
    description: str | None = None