"""Number entities for writable TROVIS values."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from trovis_modbus.metadata import NumberMetadata

from . import (
    TrovisEntity,
    component_supports_datapoint,
    ha_unit_from_number,
    require_number_metadata,
    rk1_to_rk3_indices,
)
from .coordinator import TrovisConfigEntry, TrovisCoordinator


def _number_device_class_from_number(
    number: NumberMetadata,
) -> NumberDeviceClass | None:
    """Infer a Home Assistant number device class from TROVIS metadata."""
    if number.unit == "°C":
        return NumberDeviceClass.TEMPERATURE

    # In TROVIS, K commonly represents a temperature difference or offset,
    # not an absolute temperature.
    return None


@dataclass(frozen=True, kw_only=True)
class TrovisNumberDescription(NumberEntityDescription):
    """Describe a writable number entity.

    Min/max/step/unit/writeability come from trovis-modbus. This description
    only selects the Lib field and stores Home Assistant presentation choices.
    """

    component: str
    field: str
    translation_placeholders: dict[str, str] | None = None
    requires_outdoor_sensor: bool | None = None
    requires_four_point_characteristic: bool | None = None


@dataclass(frozen=True, kw_only=True)
class TrovisHelperNumberDescription(NumberEntityDescription):
    """Describe a Home Assistant-local helper number."""

    initial_value: float


def _number(
    component: str,
    field: str,
    name: str,
    *,
    key: str | None = None,
    translation_key: str | None = None,
    translation_placeholders: dict[str, str] | None = None,
    requires_outdoor_sensor: bool | None = None,
    requires_four_point_characteristic: bool | None = None,
    enabled: bool = True,
) -> TrovisNumberDescription:
    """Return a metadata-driven number description."""
    return TrovisNumberDescription(
        key=key or field,
        translation_key=translation_key,
        translation_placeholders=translation_placeholders,
        name=name,
        component=component,
        field=field,
        requires_outdoor_sensor=requires_outdoor_sensor,
        requires_four_point_characteristic=requires_four_point_characteristic,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=enabled,
    )


_HELPERS: tuple[TrovisHelperNumberDescription, ...] = (
    TrovisHelperNumberDescription(
        key="ui_helper_selected_controller_button",
        translation_key="helper_dashboard_controller_button_clicked",
        name="Helper - Controller button currently selected on the dashboard",
        native_min_value=1,
        native_max_value=4,
        native_step=1,
        mode=NumberMode.BOX,
        initial_value=1,
    ),
)


_CONTROLLER: tuple[TrovisNumberDescription, ...] = (
    _number("controller", "summer_days_on", "Summer mode activation days"),
    _number("controller", "summer_days_off", "Summer mode deactivation days"),
    _number(
        "controller",
        "summer_outdoor_temperature_limit",
        "Summer outdoor-temperature limit",
    ),
    _number("controller", "outdoor_temperature_delay", "Outdoor-temperature delay"),
    _number("controller", "frost_protection_limit", "Frost-protection limit"),
    _number(
        "controller",
        "temperature_monitoring_deviation",
        "Temperature-monitoring deviation",
    ),
    _number(
        "controller",
        "temperature_monitoring_window",
        "Temperature-monitoring window",
    ),
    _number(
        "controller",
        "outdoor_temperature_input_range_start",
        "Outdoor-temperature input range start",
    ),
    _number(
        "controller",
        "outdoor_temperature_input_range_end",
        "Outdoor-temperature input range end",
    ),
)


def _rk_number_descriptions(index: int) -> tuple[TrovisNumberDescription, ...]:
    """Return number descriptions for one heating circuit."""
    component = f"rk{index}"
    prefix = f"rk{index}"
    placeholders = {"component": f"Rk{index}"}

    def description(
        field: str,
        name: str,
        *,
        key: str | None = None,
        requires_outdoor_sensor: bool | None = None,
        requires_four_point_characteristic: bool | None = None,
    ) -> TrovisNumberDescription:
        return _number(
            component,
            field,
            f"Rk{index} - {name}",
            key=f"{prefix}_{key or field}",
            translation_key=field,
            translation_placeholders=placeholders,
            requires_outdoor_sensor=requires_outdoor_sensor,
            requires_four_point_characteristic=(requires_four_point_characteristic),
        )

    return (
        description(
            "room_setpoint_day",
            "Room setpoint day",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=False,
        ),
        description(
            "room_setpoint_night",
            "Room setpoint night",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=False,
        ),
        description(
            "gradient",
            "Flow gradient",
            key="flow_gradient",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=False,
        ),
        description(
            "level",
            "Flow level",
            key="flow_level",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=False,
        ),
        description(
            "four_point_outdoor_temperature_1",
            "4-Point Outdoor P1",
            key="4p_outdoor_temp_p1",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_outdoor_temperature_2",
            "4-Point Outdoor P2",
            key="4p_outdoor_temp_p2",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_outdoor_temperature_3",
            "4-Point Outdoor P3",
            key="4p_outdoor_temp_p3",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_outdoor_temperature_4",
            "4-Point Outdoor P4",
            key="4p_outdoor_temp_p4",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_flow_temperature_day_1",
            "4-Point Flow daytime P1",
            key="flow_4p_day_p1",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_flow_temperature_day_2",
            "4-Point Flow daytime P2",
            key="flow_4p_day_p2",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_flow_temperature_day_3",
            "4-Point Flow daytime P3",
            key="flow_4p_day_p3",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_flow_temperature_day_4",
            "4-Point Flow daytime P4",
            key="flow_4p_day_p4",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_flow_temperature_night_1",
            "4-Point Flow nighttime P1",
            key="flow_4p_night_p1",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_flow_temperature_night_2",
            "4-Point Flow nighttime P2",
            key="flow_4p_night_p2",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_flow_temperature_night_3",
            "4-Point Flow nighttime P3",
            key="flow_4p_night_p3",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_flow_temperature_night_4",
            "4-Point Flow nighttime P4",
            key="flow_4p_night_p4",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_return_flow_temperature_1",
            "4-Point Return P1",
            key="return_4p_p1",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_return_flow_temperature_2",
            "4-Point Return P2",
            key="return_4p_p2",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_return_flow_temperature_3",
            "4-Point Return P3",
            key="return_4p_p3",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "four_point_return_flow_temperature_4",
            "4-Point Return P4",
            key="return_4p_p4",
            requires_outdoor_sensor=True,
            requires_four_point_characteristic=True,
        ),
        description(
            "minimum_flow_temperature",
            "Flow temp min",
            key="flow_temp_min",
        ),
        description(
            "maximum_flow_temperature",
            "Flow temp max",
            key="flow_temp_max",
        ),
        description(
            "return_flow_gradient",
            "Return gradient",
            key="return_gradient",
        ),
        description(
            "return_flow_level",
            "Return level",
            key="return_level",
        ),
        description(
            "return_flow_base_point",
            "Return base point",
            key="return_base_point",
        ),
        description(
            "maximum_return_flow_temperature",
            "Return temp max",
            key="return_temp_max",
        ),
        description(
            "fixed_setpoint_day",
            "Fixed flow temp daytime",
            key="flow_fixed_day",
            requires_outdoor_sensor=False,
        ),
        description(
            "fixed_setpoint_night",
            "Fixed flow temp nighttime",
            key="flow_fixed_night",
            requires_outdoor_sensor=False,
        ),
    )


def _control_parameter_number_descriptions(
    index: int,
) -> tuple[TrovisNumberDescription, ...]:
    """Return COx-F12 control-parameter descriptions for one technical Rk."""
    component = f"rk{index}"
    prefix = f"rk{index}_control_parameter"
    placeholders = {"component": f"Rk{index}"}

    def description(
        field: str,
        suffix: str,
        name: str,
    ) -> TrovisNumberDescription:
        return _number(
            component,
            field,
            f"Rk{index} {name}",
            key=f"{prefix}_{suffix}",
            translation_key=field,
            translation_placeholders=placeholders,
        )

    return (
        description("control_parameter_kp", "kp", "PI/PID gain (Kp)"),
        description("control_parameter_tn", "tn", "PI/PID reset time (Tn)"),
        description(
            "control_parameter_tv",
            "tv",
            "PI/PID derivative-action time (Tv)",
        ),
        description(
            "control_parameter_ty",
            "ty",
            "PI/PID valve transit time (Ty)",
        ),
        description(
            "control_parameter_hysteresis",
            "hysteresis",
            "two-point hysteresis",
        ),
        description(
            "control_parameter_minimum_on_time",
            "min_on_time",
            "two-point minimum ON time",
        ),
        description(
            "control_parameter_minimum_off_time",
            "min_off_time",
            "two-point minimum OFF time",
        ),
    )


_RK4_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("setpoint_day", "rk4_setpoint", "rk4_setpoint"),
    ("setpoint_night", "rk4_setpoint_night", "rk4_setpoint_night"),
    ("setpoint_min", "rk4_setpoint_min", "rk4_setpoint_min"),
    ("setpoint_max", "rk4_setpoint_max", "rk4_setpoint_max"),
    ("hysteresis", "rk4_hysteresis", "hysteresis"),
    (
        "charging_temperature_boost",
        "rk4_charging_temperature_boost",
        "charging_temperature_boost",
    ),
    (
        "storage_tank_charging_pump_lag_factor",
        "rk4_storage_tank_charging_pump_lag_factor",
        "storage_tank_charging_pump_lag_factor",
    ),
    (
        "maximum_charging_temperature",
        "rk4_maximum_charging_temperature",
        "maximum_charging_temperature",
    ),
    (
        "maximum_return_flow_temperature",
        "rk4_maximum_return_flow_temperature",
        "rk4_maximum_return_flow_temperature",
    ),
    (
        "disinfection_temperature",
        "rk4_disinfection_temperature",
        "disinfection_temperature",
    ),
    (
        "disinfection_hold_time",
        "rk4_disinfection_hold_time",
        "disinfection_hold_time",
    ),
    ("special_setpoint", "rk4_special_setpoint", "special_setpoint"),
)

_RK4: tuple[TrovisNumberDescription, ...] = tuple(
    _number(
        "rk4",
        field,
        f"Rk4 {field.replace('_', ' ')}",
        key=key,
        translation_key=translation_key,
        translation_placeholders={"component": "Rk4"},
    )
    for field, key, translation_key in _RK4_FIELDS
)


_BUFFER_TANK: tuple[TrovisNumberDescription, ...] = (
    _number(
        "buffer_tank",
        "minimum_charging_setpoint",
        "Rk1 minimum buffer charging setpoint",
        key="rk1_buffer_tank_minimum_charging_setpoint",
        translation_key="buffer_tank_minimum_charging_setpoint",
    ),
    _number(
        "buffer_tank",
        "charging_end_temperature",
        "Rk1 buffer charging end temperature",
        key="rk1_buffer_tank_charging_end_temperature",
        translation_key="buffer_tank_charging_end_temperature",
    ),
    _number(
        "buffer_tank",
        "charging_temperature_boost",
        "Rk1 buffer charging temperature boost",
        key="rk1_buffer_tank_charging_temperature_boost",
        translation_key="buffer_tank_charging_temperature_boost",
    ),
    _number(
        "buffer_tank",
        "charging_pump_lag_factor",
        "Rk1 buffer charging pump lag factor",
        key="rk1_buffer_tank_charging_pump_lag_factor",
        translation_key="buffer_tank_charging_pump_lag_factor",
    ),
)


_SOLAR: tuple[TrovisNumberDescription, ...] = (
    _number(
        "solar",
        "pump_on_temperature_difference",
        "Solar pump-on temperature difference",
        key="solar_pump_on_temperature_difference",
        translation_key="solar_pump_on_temperature_difference",
    ),
    _number(
        "solar",
        "pump_off_temperature_difference",
        "Solar pump-off temperature difference",
        key="solar_pump_off_temperature_difference",
        translation_key="solar_pump_off_temperature_difference",
    ),
    _number(
        "solar",
        "maximum_storage_temperature",
        "Solar maximum storage temperature",
        key="solar_maximum_storage_temperature",
        translation_key="solar_maximum_storage_temperature",
    ),
)


def _description_supported(
    coordinator: TrovisCoordinator,
    description: TrovisNumberDescription,
) -> bool:
    """Return whether a number field exists and applies to this circuit mode."""
    component = getattr(coordinator.device, description.component)
    if not component_supports_datapoint(component, description.field):
        return False

    if description.field.startswith("control_parameter_"):
        index = int(description.component.removeprefix("rk"))
        if description.field in {
            "control_parameter_hysteresis",
            "control_parameter_minimum_on_time",
            "control_parameter_minimum_off_time",
        }:
            return coordinator.device.two_point_control_parameters_available(index)
        return coordinator.device.control_parameters_available(index)

    has_control_mode_requirement = (
        description.requires_outdoor_sensor is not None
        or description.requires_four_point_characteristic is not None
    )
    if not has_control_mode_requirement:
        return True

    index = int(description.component.removeprefix("rk"))
    if index not in coordinator.device.room_heating_circuit_indices:
        # PRECONTROL/BUFFER slots have no room-heating setpoint-generation
        # mode, therefore no curve/fixed-setpoint configuration controls.
        return False

    uses_outdoor_sensor = coordinator.device.heating_circuit_uses_outdoor_sensor(index)

    if description.requires_outdoor_sensor is False:
        # An unknown selector keeps the established weather-compensated view
        # instead of exposing both fixed and weather-compensated controls.
        if uses_outdoor_sensor is not False:
            return False
    elif description.requires_outdoor_sensor is True:
        if uses_outdoor_sensor is False:
            return False

    requirement = description.requires_four_point_characteristic
    if requirement is None:
        return True

    uses_four_point = coordinator.device.heating_circuit_uses_four_point_characteristic(
        index
    )
    if requirement is True:
        # Four-point controls are only exposed after both selectors positively
        # identify weather compensation with a four-point characteristic.
        return uses_outdoor_sensor is True and uses_four_point is True

    # False and unknown F11 both retain the established gradient controls.
    return uses_four_point is not True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Trovis number entities."""
    coordinator = entry.runtime_data
    descriptions = list(_CONTROLLER)

    for index in rk1_to_rk3_indices(coordinator):
        descriptions.extend(_rk_number_descriptions(index))
        descriptions.extend(_control_parameter_number_descriptions(index))

    if coordinator.device.has_rk4:
        descriptions.extend(_RK4)
        descriptions.extend(_control_parameter_number_descriptions(4))

    if coordinator.device.has_buffer_tank_charging_parameters:
        descriptions.extend(_BUFFER_TANK)

    if coordinator.device.has_solar:
        descriptions.extend(_SOLAR)

    async_add_entities(
        TrovisNumber(coordinator, description)
        for description in descriptions
        if _description_supported(coordinator, description)
    )

    async_add_entities(
        TrovisNumber(coordinator, description) for description in _HELPERS
    )


class TrovisNumber(TrovisEntity, NumberEntity):
    """Trovis number entity."""

    entity_description: TrovisNumberDescription | TrovisHelperNumberDescription
    _value: float

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        description: TrovisNumberDescription | TrovisHelperNumberDescription,
    ) -> None:
        if isinstance(description, TrovisHelperNumberDescription):
            super().__init__(
                coordinator,
                description.key,
                "controller",
                "number",
                translation_key=description.translation_key,
            )
        else:
            super().__init__(
                coordinator,
                description.key,
                description.component,
                "number",
                translation_key=description.translation_key,
                translation_placeholders=description.translation_placeholders,
            )

        self.entity_description = description

        if isinstance(description, TrovisHelperNumberDescription):
            # UI helpers belong to the config entry, but not to a device.
            self._attr_device_info = None

            self._attr_native_min_value = description.native_min_value
            self._attr_native_max_value = description.native_max_value
            self._attr_native_step = description.native_step
            self._attr_mode = description.mode
            self._value = description.initial_value
            return

        number = require_number_metadata(self._subsystem, description.field)

        self._attr_native_min_value = number.min_value
        self._attr_native_max_value = number.max_value
        self._attr_native_step = number.step
        self._attr_native_unit_of_measurement = (
            description.native_unit_of_measurement or ha_unit_from_number(number)
        )
        self._attr_device_class = (
            description.device_class or _number_device_class_from_number(number)
        )
        self._attr_mode = description.mode
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )

    @property
    def native_value(self) -> float | int | None:
        """Return the current value."""
        if isinstance(self.entity_description, TrovisHelperNumberDescription):
            return self._value

        return getattr(self._subsystem, self.entity_description.field)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        if isinstance(self.entity_description, TrovisHelperNumberDescription):
            self._value = value
            self.async_write_ha_state()
            return

        await self._async_write_datapoint(self.entity_description.field, value)
