"""Primary read-only entities and diagnostic readings for TROVIS datapoints.

Normal Home Assistant entities are the complete primary representation of
library values. Climate and water-heater entities are convenience views over
the same shared components and never own exclusive datapoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Literal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from trovis_modbus import (
    OUTDOOR_TEMPERATURES,
    HeatingCircuitControlMode,
    MonthDay,
)
from trovis_modbus.metadata import EnumMetadata, NumberMetadata

from . import (
    TrovisEntity,
    component_supports_datapoint,
    ha_unit_from_number,
    require_enum_metadata,
    require_number_metadata,
    rk1_to_rk3_indices,
)
from .coordinator import TrovisConfigEntry, TrovisCoordinator
from .sensor_statistics import (
    STATISTIC_ATTRIBUTE_NAMES,
    PhysicalSensorStatisticsManager,
)
from .simulation import TrovisHeatingCurveSimulationSensor
from .simulation_dhw import TrovisDomesticHotWaterSimulationSensor

SensorValueKind = Literal[
    "plain",
    "number",
    "enum",
    "month_day",
    "heating_curves",
    "heating_operating_mode",
    "operating_mode_code",
    "system_overall_status",
]
_ROOM_HEATING_ONLY_SENSOR_FIELDS = frozenset(
    {"room_setpoint_active", "heating_curves", "operating_mode"}
)


def _sensor_device_class_from_number(
    number: NumberMetadata,
) -> SensorDeviceClass | None:
    """Infer a Home Assistant sensor device class from TROVIS metadata."""
    if number.unit == "°C":
        return SensorDeviceClass.TEMPERATURE

    if number.unit == "V":
        return SensorDeviceClass.VOLTAGE

    # In TROVIS, K commonly represents a temperature difference or offset,
    # not an absolute temperature.
    return None


@dataclass(frozen=True, kw_only=True)
class TrovisSensorDescription(SensorEntityDescription):
    """Describe a sensor reading one field of one component."""

    component: str
    field: str
    device_component: str | None = None
    value_kind: SensorValueKind = "plain"


def _number_sensor(
    component: str,
    field: str,
    name: str,
    *,
    key: str | None = None,
    translation_key: str | None = None,
    enabled: bool = True,
    entity_category: EntityCategory | None = EntityCategory.DIAGNOSTIC,
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT,
    device_class: SensorDeviceClass | None = None,
    translation_placeholders: dict[str, str] | None = None,
    device_component: str | None = None,
) -> TrovisSensorDescription:
    """Return a numeric sensor description backed by Lib metadata."""
    return TrovisSensorDescription(
        key=key or field,
        translation_key=translation_key,
        translation_placeholders=translation_placeholders,
        name=name,
        component=component,
        field=field,
        device_component=device_component,
        value_kind="number",
        device_class=device_class,
        state_class=state_class,
        entity_category=entity_category,
        entity_registry_enabled_default=enabled,
    )


def _enum_sensor(
    component: str,
    field: str,
    name: str,
    *,
    key: str | None = None,
    translation_key: str | None = None,
    enabled: bool = True,
    translation_placeholders: dict[str, str] | None = None,
) -> TrovisSensorDescription:
    """Return an enum sensor description backed by Lib metadata."""
    return TrovisSensorDescription(
        key=key or field,
        translation_key=translation_key,
        translation_placeholders=translation_placeholders,
        name=name,
        component=component,
        field=field,
        value_kind="enum",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=enabled,
    )


def _month_day_sensor(
    field: str,
    name: str,
    *,
    key: str | None = None,
    translation_key: str | None = None,
) -> TrovisSensorDescription:
    """Return a read-only representation of a recurring month/day value."""
    return TrovisSensorDescription(
        key=key or field,
        translation_key=translation_key,
        name=name,
        component="controller",
        field=field,
        value_kind="month_day",
        entity_category=EntityCategory.DIAGNOSTIC,
    )


def _operating_mode_code_sensor(
    component: str,
    key: str,
    placeholder: str,
) -> TrovisSensorDescription:
    """Return the numeric operating-mode code for one control circuit."""
    return TrovisSensorDescription(
        key=key,
        translation_key="operating_mode_code",
        translation_placeholders={"component": placeholder},
        name=f"{placeholder} - Operating mode code",
        component=component,
        field="mode",
        value_kind="operating_mode_code",
        entity_category=EntityCategory.DIAGNOSTIC,
    )


_GLOBAL: tuple[TrovisSensorDescription, ...] = (
    TrovisSensorDescription(
        key="system_code",
        translation_key="system_code",
        name="System code number",
        component="info",
        field="system_code",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TrovisSensorDescription(
        key="system_overall_status",
        translation_key="system_overall_status",
        name="System overall status",
        component="controller",
        field="system_overall_status",
        value_kind="system_overall_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TrovisSensorDescription(
        key="controller_model_code",
        translation_key="controller_model_code",
        name="Controller: Model code",
        component="info",
        field="model_code",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TrovisSensorDescription(
        key="controller_firmware",
        translation_key="controller_firmware",
        name="Controller: Firmware",
        component="info",
        field="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TrovisSensorDescription(
        key="controller_hardware_version",
        translation_key="controller_hardware_version",
        name="Controller: Hardware version",
        component="info",
        field="hardware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TrovisSensorDescription(
        key="controller_serial_number",
        translation_key="controller_serial_number",
        name="Controller: Serial number",
        component="info",
        field="serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _number_sensor(
        "sensors",
        "af1",
        "AF1 outdoor sensor 1",
        key="sensor_af1",
        translation_key="outdoor_temperature_1",
    ),
    _number_sensor(
        "sensors",
        "af2",
        "AF2 outdoor sensor 2",
        key="sensor_af2",
        translation_key="outdoor_temperature_2",
    ),
    _number_sensor(
        "sensors",
        "vf1",
        "VF1 flow sensor 1",
        key="sensor_vf1",
        translation_key="flow_temperature_1",
    ),
    _number_sensor(
        "sensors",
        "vf2",
        "VF2 flow sensor 2",
        key="sensor_vf2",
        translation_key="flow_temperature_2",
    ),
    _number_sensor(
        "sensors",
        "vf3",
        "VF3 flow sensor 3",
        key="sensor_vf3",
        translation_key="flow_temperature_3",
    ),
    _number_sensor(
        "sensors",
        "vf4",
        "VF4 flow sensor 4",
        key="sensor_vf4",
        translation_key="flow_temperature_4",
    ),
    _number_sensor(
        "sensors",
        "ruef1",
        "RüF1 return flow sensor 1",
        key="sensor_ruef1",
        translation_key="return_temperature_1",
    ),
    _number_sensor(
        "sensors",
        "ruef2",
        "RüF2 return flow sensor 2",
        key="sensor_ruef2",
        translation_key="return_temperature_2",
    ),
    _number_sensor(
        "sensors",
        "ruef3",
        "RüF3 return flow sensor 3",
        key="sensor_ruef3",
        translation_key="return_temperature_3",
    ),
    _number_sensor(
        "sensors",
        "rf1",
        "RF1 room sensor 1",
        key="sensor_rf1",
        translation_key="room_temperature_1",
    ),
    _number_sensor(
        "sensors",
        "rf2",
        "RF2 room sensor 2",
        key="sensor_rf2",
        translation_key="room_temperature_2",
    ),
    _number_sensor(
        "sensors",
        "rf3",
        "RF3 room sensor 3",
        key="sensor_rf3",
        translation_key="room_temperature_3",
    ),
    _number_sensor(
        "sensors",
        "sf1",
        "SF1 storage tank sensor 1",
        key="sensor_sf1",
        translation_key="ww_storage_temperature",
    ),
    _number_sensor(
        "sensors",
        "sf2",
        "SF2 storage tank sensor 2",
        key="sensor_sf2",
        translation_key="ww_storage_temperature_lower",
    ),
    _number_sensor(
        "sensors",
        "sf3",
        "SF3 storage tank sensor 3",
        key="sensor_sf3",
        translation_key="sf3",
    ),
    _number_sensor(
        "sensors",
        "ae1",
        "AE1 analog input 1",
        key="sensor_ae1",
        translation_key="ae1",
    ),
    _number_sensor(
        "sensors",
        "fg1",
        "FG1 remote transmitter 1",
        key="sensor_fg1",
        translation_key="fg1",
    ),
    _number_sensor(
        "sensors",
        "ae2",
        "AE2 analog input 2",
        key="sensor_ae2",
        translation_key="ae2",
    ),
    _number_sensor(
        "sensors",
        "fg2",
        "FG2 remote transmitter 2",
        key="sensor_fg2",
        translation_key="fg2",
    ),
    _number_sensor(
        "sensors",
        "ae3",
        "AE3 analog input 3",
        key="sensor_ae3",
        translation_key="ae3",
    ),
    _number_sensor(
        "sensors",
        "fg3",
        "FG3 remote transmitter 3",
        key="sensor_fg3",
        translation_key="fg3",
    ),
    _number_sensor(
        "sensors",
        "pulse_rate",
        "IMP pulse rate",
        key="sensor_imp",
        translation_key="pulse_rate",
    ),
    _number_sensor(
        "sensors",
        "analog_input_voltage",
        "AE analog input voltage",
        key="sensor_ae_voltage",
        translation_key="analog_input_voltage",
    ),
    _number_sensor(
        "sensors",
        "analog_input_current",
        "AE analog input current",
        key="sensor_ae_current",
        translation_key="analog_input_current",
    ),
    _number_sensor(
        "sensors",
        "analog_output_voltage",
        "AA1 analog output",
        key="sensor_aa1",
        translation_key="analog_output_voltage",
    ),
    _number_sensor(
        "sensors",
        "summer_outdoor_temperature_average",
        "Summer outdoor-temperature average",
        key="summer_outdoor_temperature_average",
    ),
    _number_sensor(
        "controller",
        "max_flow_setpoint",
        "Max flow setpoint",
        state_class=None,
    ),
    _enum_sensor("controller", "switch_top", "Switch top"),
    _enum_sensor("controller", "switch_middle", "Switch middle"),
    _enum_sensor("controller", "switch_bottom", "Switch bottom"),
    _number_sensor(
        "controller",
        "error_status",
        "Error status",
        state_class=None,
    ),
    _number_sensor(
        "controller",
        "special_functions",
        "Special functions",
        enabled=False,
        state_class=None,
    ),
    _number_sensor(
        "controller",
        "station_address",
        "Station address",
        state_class=None,
    ),
    _number_sensor(
        "controller",
        "error_count",
        "Error count",
        state_class=None,
    ),
)


def _rk_sensor_descriptions(index: int) -> tuple[TrovisSensorDescription, ...]:
    """Return read-only sensor descriptions for one heating circuit."""
    component = f"rk{index}"
    prefix = f"rk{index}"
    placeholders = {"component": f"Rk{index}"}
    return (
        _operating_mode_code_sensor(
            component,
            f"{prefix}_operating_mode_code",
            f"Rk{index}",
        ),
        _number_sensor(
            component,
            "valve_setpoint",
            f"Rk{index} - Valve setpoint",
            key=f"{prefix}_valve_output",
            translation_key="valve_setpoint",
            translation_placeholders=placeholders,
        ),
        _number_sensor(
            component,
            "room_setpoint_active",
            f"Rk{index} - Active room setpoint",
            key=f"{prefix}_room_setpoint_active",
            translation_key="room_setpoint_active",
            entity_category=EntityCategory.DIAGNOSTIC,
            state_class=None,
            translation_placeholders=placeholders,
        ),
        _number_sensor(
            component,
            "flow_setpoint",
            f"Rk{index} - Flow setpoint",
            key=f"{prefix}_flow_setpoint",
            translation_key="flow_setpoint",
            state_class=None,
            translation_placeholders=placeholders,
        ),
        _number_sensor(
            component,
            "return_flow_temperature_setpoint",
            f"Rk{index} - Return setpoint",
            key=f"{prefix}_return_setpoint",
            translation_key="return_flow_temperature_setpoint",
            state_class=None,
            translation_placeholders=placeholders,
        ),
        _number_sensor(
            component,
            "flow_control_deviation",
            f"Rk{index} - Flow deviation",
            key=f"{prefix}_flow_deviation",
            translation_key="flow_control_deviation",
            translation_placeholders=placeholders,
        ),
        TrovisSensorDescription(
            key=f"{prefix}_curves",
            translation_key="heating_curves",
            translation_placeholders=placeholders,
            name=f"Rk{index} - Heating curves",
            component=component,
            field="heating_curves",
            value_kind="heating_curves",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        TrovisSensorDescription(
            key=f"{prefix}_control_type",
            translation_key="heating_operating_mode",
            translation_placeholders=placeholders,
            name=f"Rk{index} - Control basis",
            component=component,
            field="operating_mode",
            value_kind="heating_operating_mode",
            device_class=SensorDeviceClass.ENUM,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    )


def _pumps_and_valves_sensor_descriptions(
    index: int,
) -> tuple[TrovisSensorDescription, ...]:
    """Return the canonical actuator sensor view for one Rk valve."""
    component = f"rk{index}"
    placeholders = {"component": f"Rk{index}"}
    return (
        _number_sensor(
            component,
            "valve_setpoint",
            f"Rk{index} - Valve setpoint",
            key=f"pumps_and_valves_rk{index}_valve_setpoint",
            translation_key="valve_setpoint",
            translation_placeholders=placeholders,
            device_component="pumps_and_valves",
        ),
    )


_RK4: tuple[TrovisSensorDescription, ...] = (
    _operating_mode_code_sensor(
        "rk4",
        "rk4_operating_mode_code",
        "Rk4",
    ),
    _number_sensor(
        "rk4",
        "setpoint_active",
        "Rk4 active domestic hot-water setpoint",
        key="rk4_setpoint_active",
        translation_key="rk4_setpoint_active",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=None,
        translation_placeholders={"component": "Rk4"},
    ),
    _enum_sensor(
        "rk4",
        "storage_status",
        "Rk4 storage status",
        key="rk4_storage_status",
        translation_key="storage_status",
        translation_placeholders={"component": "Rk4"},
    ),
    _number_sensor(
        "rk4",
        "active_charging_setpoint",
        "Rk4 active charging set point",
        key="rk4_active_charging_setpoint",
        translation_key="active_charging_setpoint",
        state_class=None,
        translation_placeholders={"component": "Rk4"},
    ),
    _number_sensor(
        "rk4",
        "control_deviation",
        "Rk4 control deviation",
        key="rk4_control_deviation",
        translation_key="control_deviation",
        translation_placeholders={"component": "Rk4"},
    ),
)

_BUFFER_TANK: tuple[TrovisSensorDescription, ...] = (
    _enum_sensor(
        "buffer_tank",
        "status",
        "Rk1 buffer tank status",
        key="rk1_buffer_tank_status",
        translation_key="buffer_tank_status",
    ),
)

_SOLAR: tuple[TrovisSensorDescription, ...] = (
    _number_sensor(
        "solar",
        "operating_hours",
        "Solar operating hours",
        key="solar_operating_hours",
        translation_key="solar_operating_hours",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
)


def _description_supported(
    coordinator: TrovisCoordinator,
    description: TrovisSensorDescription,
) -> bool:
    """Return whether a sensor description applies to this device."""
    if description.component == "sensors":
        if description.field not in coordinator.device.available_sensor_keys:
            return False
    if description.component in {"rk1", "rk2", "rk3"}:
        index = int(description.component[-1])
        if (
            description.field in _ROOM_HEATING_ONLY_SENSOR_FIELDS
            and index not in coordinator.device.room_heating_circuit_indices
        ):
            return False

    if description.value_kind in (
        "plain",
        "heating_curves",
        "heating_operating_mode",
        "system_overall_status",
    ):
        return True
    component = getattr(coordinator.device, description.component)
    return component_supports_datapoint(component, description.field)


def _uses_physical_sensor_statistics(description: TrovisSensorDescription) -> bool:
    """Return whether this is a numeric physical measurement/input-output."""
    return (
        description.component == "sensors"
        and description.value_kind == "number"
        and description.state_class == SensorStateClass.MEASUREMENT
        and description.field != "summer_outdoor_temperature_average"
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Trovis sensors."""
    coordinator = entry.runtime_data
    descriptions = list(_GLOBAL)
    for index in rk1_to_rk3_indices(coordinator):
        descriptions.extend(_rk_sensor_descriptions(index))
        descriptions.extend(_pumps_and_valves_sensor_descriptions(index))
    if coordinator.device.has_rk4:
        descriptions.extend(_RK4)
    if coordinator.device.has_buffer_tank_circuit:
        descriptions.extend(_BUFFER_TANK)
    if coordinator.device.has_solar:
        descriptions.extend(_SOLAR)
    statistics_manager = PhysicalSensorStatisticsManager(hass)
    entities: list[SensorEntity] = [
        TrovisSensor(
            coordinator,
            description,
            statistics_manager=(
                statistics_manager
                if _uses_physical_sensor_statistics(description)
                else None
            ),
        )
        for description in descriptions
        if _description_supported(coordinator, description)
    ]
    entities.extend(
        TrovisHeatingCurveSimulationSensor(coordinator, index)
        for index in coordinator.device.room_heating_circuit_indices
    )
    if coordinator.device.has_rk4:
        entities.append(TrovisDomesticHotWaterSimulationSensor(coordinator))
    async_add_entities(entities)
    entry.async_on_unload(statistics_manager.stop)
    statistics_manager.start()


class TrovisSensor(TrovisEntity, SensorEntity):
    """A single value read from a component field."""

    _unrecorded_attributes = STATISTIC_ATTRIBUTE_NAMES

    entity_description: TrovisSensorDescription

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        description: TrovisSensorDescription,
        *,
        statistics_manager: PhysicalSensorStatisticsManager | None = None,
    ) -> None:
        super().__init__(
            coordinator,
            description.key,
            description.component,
            "sensor",
            translation_key=description.translation_key,
            translation_placeholders=description.translation_placeholders,
            device_component=description.device_component,
        )
        self.entity_description = description
        self._statistics_manager = statistics_manager
        self._enum_metadata: EnumMetadata | None = None
        self._key_by_value: dict[int, str] = {}
        if description.value_kind == "number":
            if description.component == "sensors":
                number = coordinator.device.sensor_number_metadata(description.field)
            else:
                number = require_number_metadata(self._subsystem, description.field)
            self._attr_native_unit_of_measurement = (
                description.native_unit_of_measurement or ha_unit_from_number(number)
            )
            self._attr_device_class = (
                description.device_class or _sensor_device_class_from_number(number)
            )
        elif description.value_kind == "enum":
            self._enum_metadata = require_enum_metadata(
                self._subsystem,
                description.field,
            )
            self._key_by_value = {
                int(option.value): option.key for option in self._enum_metadata.options
            }
            self._attr_options = [option.key for option in self._enum_metadata.options]
            self._attr_device_class = SensorDeviceClass.ENUM
        elif description.value_kind == "heating_operating_mode":
            self._attr_options = [mode.value for mode in HeatingCircuitControlMode]
            self._attr_device_class = SensorDeviceClass.ENUM
        elif description.value_kind == "heating_curves":
            self._attr_options = ["error", "calculated"]
            self._attr_device_class = SensorDeviceClass.ENUM

        self._attr_state_class = description.state_class
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )

    async def async_added_to_hass(self) -> None:
        """Register physical measurements for recorder-backed statistics."""
        await super().async_added_to_hass()

        if self._statistics_manager is None:
            return
        entity_id = self.entity_id
        self._statistics_manager.register(self)
        self.async_on_remove(lambda: self._statistics_manager.unregister(entity_id))

    def _heating_operating_mode(self) -> HeatingCircuitControlMode | None:
        """Return the active setpoint-generation mode for this Rk entity."""
        index = int(self.entity_description.component.removeprefix("rk"))
        return self.coordinator.device.heating_circuit_operating_mode(index)

    def _heating_curve_attributes(
        self,
    ) -> dict[str, list[int] | list[float]] | None:
        """Return parallel x/day/night/active flow and return-curve lists."""
        operating_mode = self._heating_operating_mode()
        if operating_mode is None:
            return None
        flow_curve = self._subsystem.heating_curve(
            operating_mode=operating_mode,
            curve="flow",
        )
        flow_curve_day = self._subsystem.heating_curve(
            mode="day",
            operating_mode=operating_mode,
            curve="flow",
        )
        flow_curve_night = self._subsystem.heating_curve(
            mode="night",
            operating_mode=operating_mode,
            curve="flow",
        )
        return_curve = self._subsystem.heating_curve(
            operating_mode=operating_mode,
            curve="return",
        )
        return_curve_day = self._subsystem.heating_curve(
            mode="day",
            operating_mode=operating_mode,
            curve="return",
        )
        return_curve_night = self._subsystem.heating_curve(
            mode="night",
            operating_mode=operating_mode,
            curve="return",
        )
        if (
            flow_curve is None
            or flow_curve_day is None
            or flow_curve_night is None
            or return_curve is None
            or return_curve_day is None
            or return_curve_night is None
        ):
            return None
        curves = (
            flow_curve,
            flow_curve_day,
            flow_curve_night,
            return_curve,
            return_curve_day,
            return_curve_night,
        )
        if any(len(curve) != len(OUTDOOR_TEMPERATURES) for curve in curves):
            return None
        return {
            "x_values": list(OUTDOOR_TEMPERATURES),
            "flow_curve": flow_curve,
            "flow_curve_day": flow_curve_day,
            "flow_curve_night": flow_curve_night,
            "return_curve": return_curve,
            "return_curve_day": return_curve_day,
            "return_curve_night": return_curve_night,
        }

    @property
    def native_value(self) -> object:
        """Return the current value in Home Assistant form."""
        if self.entity_description.value_kind == "heating_curves":
            if self._heating_curve_attributes() is None:
                return "error"
            return "calculated"

        if self.entity_description.value_kind == "heating_operating_mode":
            operating_mode = self._heating_operating_mode()
            return operating_mode.value if operating_mode is not None else None
        if self.entity_description.value_kind == "system_overall_status":
            value = self.coordinator.device.system_overall_status
            return int(value) if value is not None else None

        if self.entity_description.component == "sensors":
            value = self.coordinator.device.sensor_value(self.entity_description.field)
        else:
            value = getattr(self._subsystem, self.entity_description.field)

        if value is None:
            return None
        if self.entity_description.value_kind == "operating_mode_code":
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        if self.entity_description.value_kind == "month_day":
            if not isinstance(value, MonthDay):
                return None
            return f"{value.month:02d}-{value.day:02d}"
        if self.entity_description.value_kind == "enum":
            try:
                return self._key_by_value.get(int(value))
            except (TypeError, ValueError):
                return None

        if isinstance(value, IntEnum):
            return value.name.lower()

        return value

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Expose derived curves, physical statistics, or recurring dates."""
        if self.entity_description.value_kind == "heating_curves":
            return self._heating_curve_attributes()

        if self._statistics_manager is not None:
            return self._statistics_manager.attributes(self.entity_id)

        if self.entity_description.value_kind != "month_day":
            return None
        value = getattr(self._subsystem, self.entity_description.field)
        if not isinstance(value, MonthDay):
            return None

        return {"month": value.month, "day": value.day}
