"""Climate platform for weather-compensated room-heating circuits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from trovis_modbus import HeatingCircuit, OperatingMode

from . import (
    TrovisEntity,
    ha_unit_from_number,
    require_number_metadata,
)
from .coordinator import TrovisConfigEntry, TrovisCoordinator

_TO_HVAC = {
    OperatingMode.STANDBY: HVACMode.OFF,
    OperatingMode.AUTOMATIC: HVACMode.AUTO,
    OperatingMode.PROGRAM: HVACMode.AUTO,
    OperatingMode.DAY: HVACMode.HEAT,
    OperatingMode.NIGHT: HVACMode.HEAT,
    OperatingMode.MANUAL: HVACMode.HEAT,
}
_FROM_HVAC = {
    HVACMode.OFF: OperatingMode.STANDBY,
    HVACMode.AUTO: OperatingMode.AUTOMATIC,
    HVACMode.HEAT: OperatingMode.DAY,
}


@dataclass(frozen=True, kw_only=True)
class TrovisClimateDescription(ClimateEntityDescription):
    """Describes a climate entity for one heating circuit."""

    component: str


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a climate entity per weather-compensated heating circuit."""
    coordinator = entry.runtime_data
    async_add_entities(
        TrovisHeatingCircuitClimate(coordinator, index)
        for index in coordinator.device.room_heating_circuit_indices
        if (
            coordinator.device.heating_circuit_uses_outdoor_sensor(index) is not False
            and coordinator.device.heating_circuit_uses_four_point_characteristic(index)
            is not True
        )
    )


class TrovisHeatingCircuitClimate(TrovisEntity, ClimateEntity):
    """A heating circuit as a thermostat (room setpoint + mode)."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_min_temp = 5
    _attr_max_temp = 30
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator: TrovisCoordinator, index: int) -> None:
        description = TrovisClimateDescription(
            key=f"rk{index}",
            translation_key=f"rk{index}",
            component=f"rk{index}",
        )
        super().__init__(
            coordinator,
            key=description.key,
            component=description.component,
            platform="climate",
            translation_key=description.translation_key,
        )
        self.entity_description = description
        target_metadata = require_number_metadata(self._circuit, "room_setpoint_day")

        self._attr_min_temp = target_metadata.min_value
        self._attr_max_temp = target_metadata.max_value
        self._attr_target_temperature_step = target_metadata.step
        self._attr_temperature_unit = (
            ha_unit_from_number(target_metadata) or UnitOfTemperature.CELSIUS
        )

    @property
    def _circuit(self) -> HeatingCircuit:
        return self._subsystem  # type: ignore[return-value]

    # @property
    # def current_temperature(self) -> float | None:
    #     return self._circuit.room_temperature
    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature.
        Physical room sensors are exposed centrally through the Sensors component.
        They are not assigned to heating circuits here because the mapping depends
        on the configured hydraulic scheme.
        --> ToDo: Evaluate if hard coded connection to heating circuits, likely no
        """
        return None

    @property
    def target_temperature(self) -> float | None:
        return self._circuit.room_setpoint_active

    @property
    def hvac_mode(self) -> HVACMode | None:
        mode = self._circuit.mode
        return _TO_HVAC.get(mode) if mode is not None else None

    @property
    def hvac_action(self) -> HVACAction | None:
        if self._circuit.mode is OperatingMode.STANDBY:
            return HVACAction.OFF
        if self._circuit.pump_running is None:
            return None
        return HVACAction.HEATING if self._circuit.pump_running else HVACAction.IDLE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        await self._async_write_datapoint("room_setpoint_day", temperature)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set a new HVAC mode."""
        if hvac_mode not in _FROM_HVAC:
            raise HomeAssistantError(f"Unsupported TROVIS HVAC mode: {hvac_mode}")

        await self._async_write_datapoint("mode", _FROM_HVAC[hvac_mode])
