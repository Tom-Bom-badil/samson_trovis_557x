"""Water heater platform - the domestic-hot-water control circuit Rk4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityDescription,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from trovis_modbus import DomesticHotWater, OperatingMode

from . import (
    TrovisEntity,
    ha_unit_from_number,
    require_enum_metadata,
    require_number_metadata,
)
from .coordinator import TrovisConfigEntry, TrovisCoordinator

# Operation-list labels <-> controller modes.
_MODES = {
    "auto": OperatingMode.AUTOMATIC,
    "on": OperatingMode.DAY,
    "off": OperatingMode.STANDBY,
}
_REVERSE = {mode: label for label, mode in _MODES.items()}


@dataclass(frozen=True, kw_only=True)
class TrovisWaterHeaterDescription(WaterHeaterEntityDescription):
    """Describes the domestic hot water entity."""

    component: str


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the domestic hot-water entity."""
    coordinator = entry.runtime_data
    if not coordinator.device.has_rk4:
        return

    async_add_entities([TrovisDomesticHotWaterEntity(coordinator)])


class TrovisDomesticHotWaterEntity(TrovisEntity, WaterHeaterEntity):
    """Domestic hot water as a water heater."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    _attr_operation_list = list(_MODES)

    def __init__(self, coordinator: TrovisCoordinator) -> None:
        description = TrovisWaterHeaterDescription(
            key="rk4",
            translation_key="rk4",
            component="rk4",
        )
        super().__init__(
            coordinator,
            key=description.key,
            component=description.component,
            platform="water_heater",
            translation_key=description.translation_key,
        )
        self.entity_description = description
        temperature_metadata = require_number_metadata(
            self._domestic_hot_water, "setpoint_day"
        )
        enum_metadata = require_enum_metadata(self._domestic_hot_water, "mode")

        self._enum_metadata = enum_metadata
        self._option_by_key = {option.key: option for option in enum_metadata.options}
        self._key_by_value = {
            int(option.value): option.key for option in enum_metadata.options
        }

        self._attr_operation_list = list(self._option_by_key)
        self._attr_min_temp = temperature_metadata.min_value
        self._attr_max_temp = temperature_metadata.max_value
        self._attr_target_temperature_step = temperature_metadata.step
        self._attr_temperature_unit = (
            ha_unit_from_number(temperature_metadata) or UnitOfTemperature.CELSIUS
        )

    @property
    def _domestic_hot_water(self) -> DomesticHotWater:
        return self._subsystem  # type: ignore[return-value]

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.sensors.sf1

    @property
    def target_temperature(self) -> float | None:
        return self._domestic_hot_water.setpoint_active

    @property
    def min_temp(self) -> float:
        return self._domestic_hot_water.setpoint_min or 20.0

    @property
    def max_temp(self) -> float:
        return self._domestic_hot_water.setpoint_max or 90.0

    @property
    def current_operation(self) -> str | None:
        """Return the current operation mode."""
        mode = self._domestic_hot_water.mode
        if mode is None:
            return None

        try:
            return self._key_by_value.get(int(mode))
        except (TypeError, ValueError):
            return None

    @property
    def operation_list(self) -> list[str]:
        """Return the list of available operation modes."""
        return list(self._option_by_key)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        await self._async_write_datapoint("setpoint_day", temperature)

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set a new operation mode."""
        try:
            selected = self._option_by_key[operation_mode]
        except KeyError as err:
            raise HomeAssistantError(
                f"Unsupported TROVIS operation mode: {operation_mode}"
            ) from err

        await self._async_write_datapoint(
            "mode",
            self._enum_metadata.enum_type(selected.value),
        )
