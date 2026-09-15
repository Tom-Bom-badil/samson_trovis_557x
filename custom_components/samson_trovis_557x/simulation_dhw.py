"""Home Assistant-local Rk4 domestic-hot-water simulation helper."""

from __future__ import annotations

from dataclasses import dataclass

from . import TrovisEntity
from .coordinator import TrovisCoordinator
from .simulation import TrovisHeatingCurveSimulationSensor


@dataclass(frozen=True, slots=True)
class DomesticHotWaterSimulationParameters:
    """Local snapshot of the Rk4 values used by the dashboard simulation."""

    setpoint_day: float | None
    setpoint_night: float | None
    hysteresis: float | None
    charging_temperature_boost: float | None
    maximum_charging_temperature: float | None
    maximum_return_flow_temperature: float | None


_DHW_PARAMETER_NAMES = tuple(DomesticHotWaterSimulationParameters.__annotations__)
_DHW_SIMULATION_FIELDS = frozenset(_DHW_PARAMETER_NAMES)
_DHW_UNRECORDED_ATTRIBUTES = frozenset(("changed_fields", *_DHW_PARAMETER_NAMES))


class TrovisDomesticHotWaterSimulationSensor(TrovisHeatingCurveSimulationSensor):
    """Local simulation state for the TROVIS Rk4 domestic-hot-water circuit."""

    _unrecorded_attributes = _DHW_UNRECORDED_ATTRIBUTES

    def __init__(self, coordinator: TrovisCoordinator) -> None:
        # Keep this helper compatible with the existing simulation entity actions by
        # deriving from the heating-circuit helper, but initialize the shared
        # TrovisEntity layer directly because Rk4 has no heating-curve parameters.
        TrovisEntity.__init__(
            self,
            coordinator,
            "ui_helper_rk4_simulation_values",
            "rk4",
            "sensor",
            translation_key="ui_helper_simulation_values",
            translation_placeholders={"component": "Rk4"},
        )

        # Dashboard-local helper: keep it out of the TROVIS device views.
        self._attr_device_info = None

        # The inherited validation path references this only for an invalid
        # field; Rk4 has no heating-curve control mode.
        self._operating_mode = None

        self._baseline = self._snapshot_parameters()
        self._parameters = self._baseline

    def _snapshot_parameters(self) -> DomesticHotWaterSimulationParameters:
        """Return the current live Rk4 values used by the simulation."""
        return DomesticHotWaterSimulationParameters(
            setpoint_day=self._subsystem.setpoint_day,
            setpoint_night=self._subsystem.setpoint_night,
            hysteresis=self._subsystem.hysteresis,
            charging_temperature_boost=self._subsystem.charging_temperature_boost,
            maximum_charging_temperature=self._subsystem.maximum_charging_temperature,
            maximum_return_flow_temperature=(
                self._subsystem.maximum_return_flow_temperature
            ),
        )

    @property
    def changed_fields(self) -> tuple[str, ...]:
        """Return Rk4 fields that differ from the initial snapshot."""
        return tuple(
            name
            for name in _DHW_PARAMETER_NAMES
            if getattr(self._parameters, name) != getattr(self._baseline, name)
        )

    def _allowed_simulation_fields(self) -> frozenset[str]:
        """Return the fields that can be changed in the Rk4 simulation."""
        return _DHW_SIMULATION_FIELDS

    async def async_reset_simulation(self) -> None:
        """Replace baseline and simulation with the current live Rk4 values."""
        # The inherited validation path references this only for an invalid
        # field; Rk4 has no heating-curve control mode.
        self._operating_mode = None

        self._baseline = self._snapshot_parameters()
        self._parameters = self._baseline
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose the Rk4 simulation snapshot."""
        return {
            "changed_fields": list(self.changed_fields),
            **{name: getattr(self._parameters, name) for name in _DHW_PARAMETER_NAMES},
        }
