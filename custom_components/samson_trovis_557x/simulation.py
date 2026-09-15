"""Home Assistant-local heating-curve simulation helpers."""

from __future__ import annotations

from dataclasses import fields, replace

from homeassistant.components.sensor import SensorEntity
from homeassistant.exceptions import ServiceValidationError
from trovis_modbus import OUTDOOR_TEMPERATURES, HeatingCircuitControlMode
from trovis_modbus.heating_curve import (
    HeatingCurveParameters,
    calculate_heating_curve,
)

from . import TrovisEntity, require_number_metadata
from .const import DOMAIN
from .coordinator import TrovisCoordinator

_PARAMETER_NAMES = tuple(field.name for field in fields(HeatingCurveParameters))
_CURVE_ATTRIBUTE_NAMES = (
    "x_values",
    "flow_curve",
    "flow_curve_day",
    "flow_curve_night",
    "return_curve",
    "return_curve_day",
    "return_curve_night",
)
_UNRECORDED_ATTRIBUTES = frozenset(
    (
        "control_mode",
        "calculation_state",
        "changed_fields",
        *_PARAMETER_NAMES,
        *_CURVE_ATTRIBUTE_NAMES,
    )
)

SIMULATION_PARAMETER_FIELDS = (
    "gradient",
    "level",
    "room_setpoint_day",
    "room_setpoint_night",
    "minimum_flow_temperature",
    "maximum_flow_temperature",
    "return_flow_gradient",
    "return_flow_level",
    "return_flow_base_point",
    "maximum_return_flow_temperature",
    "four_point_outdoor_temperature_1",
    "four_point_outdoor_temperature_2",
    "four_point_outdoor_temperature_3",
    "four_point_outdoor_temperature_4",
    "four_point_flow_temperature_day_1",
    "four_point_flow_temperature_day_2",
    "four_point_flow_temperature_day_3",
    "four_point_flow_temperature_day_4",
    "four_point_flow_temperature_night_1",
    "four_point_flow_temperature_night_2",
    "four_point_flow_temperature_night_3",
    "four_point_flow_temperature_night_4",
    "four_point_return_flow_temperature_1",
    "four_point_return_flow_temperature_2",
    "four_point_return_flow_temperature_3",
    "four_point_return_flow_temperature_4",
    "fixed_setpoint_day",
    "fixed_setpoint_night",
)

_COMMON_FLOW_LIMIT_FIELDS = frozenset(
    {
        "minimum_flow_temperature",
        "maximum_flow_temperature",
    }
)
_SIMULATION_FIELDS_BY_MODE = {
    HeatingCircuitControlMode.HEATING_CURVE: _COMMON_FLOW_LIMIT_FIELDS
    | frozenset(
        {
            "room_setpoint_day",
            "room_setpoint_night",
            "gradient",
            "level",
            "return_flow_gradient",
            "return_flow_level",
            "return_flow_base_point",
            "maximum_return_flow_temperature",
        }
    ),
    HeatingCircuitControlMode.FOUR_POINT: _COMMON_FLOW_LIMIT_FIELDS
    | frozenset(
        {
            "four_point_outdoor_temperature_1",
            "four_point_outdoor_temperature_2",
            "four_point_outdoor_temperature_3",
            "four_point_outdoor_temperature_4",
            "four_point_flow_temperature_day_1",
            "four_point_flow_temperature_day_2",
            "four_point_flow_temperature_day_3",
            "four_point_flow_temperature_day_4",
            "four_point_flow_temperature_night_1",
            "four_point_flow_temperature_night_2",
            "four_point_flow_temperature_night_3",
            "four_point_flow_temperature_night_4",
            "four_point_return_flow_temperature_1",
            "four_point_return_flow_temperature_2",
            "four_point_return_flow_temperature_3",
            "four_point_return_flow_temperature_4",
        }
    ),
    HeatingCircuitControlMode.FIXED_SETPOINT: _COMMON_FLOW_LIMIT_FIELDS
    | frozenset(
        {
            "fixed_setpoint_day",
            "fixed_setpoint_night",
        }
    ),
}


class TrovisHeatingCurveSimulationSensor(TrovisEntity, SensorEntity):
    """Local simulation state for one TROVIS room-heating circuit."""

    _unrecorded_attributes = _UNRECORDED_ATTRIBUTES
    _attr_entity_registry_visible_default = False

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        index: int,
    ) -> None:
        component = f"rk{index}"
        super().__init__(
            coordinator,
            f"ui_helper_rk{index}_simulation_values",
            component,
            "sensor",
            translation_key="ui_helper_simulation_values",
            translation_placeholders={"component": f"Rk{index}"},
        )

        # Dashboard-local helper: keep it out of the TROVIS device views.
        self._attr_device_info = None

        self._index = index
        self._baseline = self._subsystem.heating_curve_parameters()
        self._parameters = self._baseline
        self._operating_mode = coordinator.device.heating_circuit_operating_mode(index)

    @property
    def changed_fields(self) -> tuple[str, ...]:
        """Return parameter fields that differ from the initial snapshot."""
        return tuple(
            name
            for name in _PARAMETER_NAMES
            if getattr(self._parameters, name) != getattr(self._baseline, name)
        )

    @property
    def native_value(self) -> int:
        """Return the number of simulation parameters changed from baseline."""
        return len(self.changed_fields)

    def _allowed_simulation_fields(self) -> frozenset[str]:
        """Return fields that belong to this helper's snapshotted control mode."""
        if self._operating_mode is None:
            return frozenset()
        return _SIMULATION_FIELDS_BY_MODE.get(
            self._operating_mode,
            frozenset(),
        )

    def _validate_simulation_value(self, field: str, value: float) -> None:
        """Validate one local simulation value against mode and Lib metadata."""
        if field not in self._allowed_simulation_fields():
            mode = (
                self._operating_mode.value
                if isinstance(self._operating_mode, HeatingCircuitControlMode)
                else "unknown"
            )
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="simulation_field_not_available",
                translation_placeholders={
                    "field": field,
                    "mode": mode,
                    "entity_id": self.entity_id,
                },
            )

        try:
            metadata = require_number_metadata(self._subsystem, field)
        except ValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="simulation_field_not_numeric",
                translation_placeholders={
                    "field": field,
                    "entity_id": self.entity_id,
                },
            ) from err

        if (
            metadata.min_value is not None
            and value < metadata.min_value
            or metadata.max_value is not None
            and value > metadata.max_value
        ):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="simulation_value_out_of_range",
                translation_placeholders={
                    "value": str(value),
                    "field": field,
                    "entity_id": self.entity_id,
                    "min_value": str(metadata.min_value),
                    "max_value": str(metadata.max_value),
                },
            )

    async def async_set_simulation_value(
        self,
        field: str,
        value: float,
    ) -> None:
        """Change one local simulation parameter without writing Modbus."""
        self._validate_simulation_value(field, value)
        self._parameters = replace(
            self._parameters,
            **{field: value},
        )
        self.async_write_ha_state()

    async def async_reset_simulation(self) -> None:
        """Replace baseline and simulation with the current live Rk values."""
        self._baseline = self._subsystem.heating_curve_parameters()
        self._parameters = self._baseline
        self._operating_mode = self.coordinator.device.heating_circuit_operating_mode(
            self._index
        )
        self.async_write_ha_state()

    def _curve_attributes(self) -> dict[str, object]:
        """Calculate the simulated flow and return characteristics."""
        operating_mode = self._operating_mode
        if operating_mode is None:
            return {"calculation_state": "error"}

        curves = {
            "flow_curve": calculate_heating_curve(
                self._parameters,
                operating_mode=operating_mode,
                curve="flow",
            ),
            "flow_curve_day": calculate_heating_curve(
                self._parameters,
                "day",
                operating_mode=operating_mode,
                curve="flow",
            ),
            "flow_curve_night": calculate_heating_curve(
                self._parameters,
                "night",
                operating_mode=operating_mode,
                curve="flow",
            ),
            "return_curve": calculate_heating_curve(
                self._parameters,
                operating_mode=operating_mode,
                curve="return",
            ),
            "return_curve_day": calculate_heating_curve(
                self._parameters,
                "day",
                operating_mode=operating_mode,
                curve="return",
            ),
            "return_curve_night": calculate_heating_curve(
                self._parameters,
                "night",
                operating_mode=operating_mode,
                curve="return",
            ),
        }

        if any(curve is None for curve in curves.values()):
            return {"calculation_state": "error"}

        if any(
            len(curve) != len(OUTDOOR_TEMPERATURES)
            for curve in curves.values()
            if curve is not None
        ):
            return {"calculation_state": "error"}

        return {
            "calculation_state": "calculated",
            "x_values": list(OUTDOOR_TEMPERATURES),
            **curves,
        }

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose the simulation snapshot and its calculated characteristics."""
        operating_mode = self._operating_mode
        attributes: dict[str, object] = {
            "control_mode": (
                operating_mode.value
                if isinstance(operating_mode, HeatingCircuitControlMode)
                else None
            ),
            "changed_fields": list(self.changed_fields),
        }
        attributes.update(
            {name: getattr(self._parameters, name) for name in _PARAMETER_NAMES}
        )
        attributes.update(self._curve_attributes())
        return attributes
