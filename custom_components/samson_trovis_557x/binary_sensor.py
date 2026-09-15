"""Binary sensors for read-only TROVIS operating and control states."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import (
    TrovisEntity,
    component_supports_datapoint,
    rk1_to_rk3_indices,
)
from .coordinator import TrovisConfigEntry, TrovisCoordinator


@dataclass(frozen=True, kw_only=True)
class TrovisBinaryDescription(BinarySensorEntityDescription):
    """Describe a binary sensor reading one boolean Lib field."""

    component: str
    field: str
    device_component: str | None = None


def _binary(
    component: str,
    field: str,
    name: str,
    device_class: BinarySensorDeviceClass | None = None,
    *,
    key: str | None = None,
    translation_key: str | None = None,
    translation_placeholders: dict[str, str] | None = None,
    enabled: bool = True,
    device_component: str | None = None,
) -> TrovisBinaryDescription:
    """Return a binary-sensor description."""
    return TrovisBinaryDescription(
        key=key or f"{component}_{field}",
        translation_key=translation_key,
        translation_placeholders=translation_placeholders,
        name=name,
        component=component,
        field=field,
        device_component=device_component,
        device_class=device_class,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=enabled,
    )


_CONTROLLER: tuple[TrovisBinaryDescription, ...] = (
    _binary(
        "controller",
        "general_fault",
        "Fault",
        BinarySensorDeviceClass.PROBLEM,
        key="general_fault",
    ),
    _binary("controller", "summer_active", "Summer mode", key="summer_active"),
    # obsolete
    # _binary(
    #     "controller",
    #     "data_entry_active",
    #     "Data entry active",
    #     key="data_entry_active",
    #     enabled=False,
    # ),
    # _binary(
    #     "controller",
    #     "data_entry_performed",
    #     "Data entry performed",
    #     key="data_entry_performed",
    #     enabled=False,
    # ),
    # _binary(
    #     "controller",
    #     "global_level_autark",
    #     "Global control autonomous",
    #     key="global_level_autark",
    #     enabled=False,
    # ),
    # _binary(
    #     "controller",
    #     "outdoor_temperature_control_autonomous",
    #     "Outdoor-temperature control autonomous",
    #     key="outdoor_temperature_control_autonomous",
    #     enabled=False,
    # ),
    _binary(
        "controller",
        "any_circuit_not_automatic",
        "At least one circuit not automatic",
        key="any_circuit_not_automatic",
    ),
    _binary(
        "controller",
        "rotary_switch_not_automatic",
        "At least one rotary switch not automatic",
        key="rotary_switch_not_automatic",
    ),
)


_ROOM_HEATING_ONLY_BINARY_FIELDS = frozenset(
    {
        "day_active",
        "night_active",
        "hold_active",
        "setback_active",
        "heat_up_active",
        "outdoor_temperature_deactivation",
    }
)


_CIRCUIT_STATES: tuple[
    tuple[str, str, str, BinarySensorDeviceClass | None, bool], ...
] = (
    (
        "frost_protection",
        "frost_protection",
        "Frost protection",
        BinarySensorDeviceClass.COLD,
        True,
    ),
    ("standby", "mode_standby", "Mode standby", None, True),
    ("manual_active", "mode_manual", "Mode manual", None, True),
    ("automatic", "mode_automatic", "Mode automatic", None, True),
    ("day_active", "mode_day", "Mode day", None, True),
    ("night_active", "mode_night", "Mode night", None, True),
    ("hold_active", "mode_hold", "Mode hold", None, True),
    ("setback_active", "mode_setback", "Mode setback", None, True),
    (
        "heat_up_active",
        "mode_heat_up",
        "Mode heat-up",
        BinarySensorDeviceClass.HEAT,
        True,
    ),
    (
        "return_limit_active",
        "return_limit_active",
        "Return limit active",
        None,
        True,
    ),
    (
        "outdoor_temperature_deactivation",
        "outdoor_temp_cutoff_active",
        "Outdoor temp cutoff active",
        None,
        True,
    ),
    (
        "valve_closing",
        "valve_closing",
        "Valve closing",
        None,  # BinarySensorDeviceClass.MOVING,
        True,
    ),
    (
        "valve_opening",
        "valve_opening",
        "Valve opening",
        None,  # BinarySensorDeviceClass.MOVING,
        True,
    ),
    # These should not be needed in the integration itself.
    # The Library handles enablement of write-access for specific cases.
    # (
    #     "mode_control_autonomous",
    #     "control_mode_autonomous",
    #     "Autonomous operating mode control",
    #     None,
    #     False,
    # ),
    # (
    #     "valve_control_autonomous",
    #     "control_valve_autonomous",
    #     "Autonomous valve control",
    #     None,
    #     False,
    # ),
    # (
    #     "pump_control_autonomous",
    #     "control_pump_autonomous",
    #     "Autonomous pump control",
    #     None,
    #     False,
    # ),
    # (
    #     "flow_setpoint_control_autonomous",
    #     "control_flow_setpoint_autonomous",
    #     "Autonomous flow setpoint control",
    #     None,
    #     False,
    # ),
    # (
    #     "return_flow_temperature_setpoint_control_autonomous",
    #     "control_return_setpoint_autonomous",
    #     "Autonomous return setpoint control",
    #     None,
    #     False,
    # ),
    # (
    #     "room_setpoint_control_autonomous",
    #     "control_room_setpoint_autonomous",
    #     "Autonomous room setpoint control",
    #     None,
    #     False,
    # ),
)


def _pumps_and_valves_rk_binary_descriptions(
    index: int,
) -> tuple[TrovisBinaryDescription, ...]:
    """Return the canonical pump/valve state view for one technical Rk."""
    component = f"rk{index}"
    # valve_placeholders = {"component": f"Rk{index}"}

    return (
        _binary(
            component,
            "pump_running",
            f"UP{index} pump running",
            key=f"pumps_and_valves_up{index}",
            translation_key="pump_running",
            translation_placeholders={"component": f"UP{index}"},
            device_component="pumps_and_valves",
        ),
        # removed, belongs into heating ncircuit
        # _binary(
        #     component,
        #     "valve_closing",
        #     f"Rk{index} valve closing",
        #     key=f"pumps_and_valves_rk{index}_valve_closing",
        #     translation_key="valve_closing",
        #     translation_placeholders=valve_placeholders,
        #     device_component="pumps_and_valves",
        # ),
        # _binary(
        #     component,
        #     "valve_opening",
        #     f"Rk{index} valve opening",
        #     key=f"pumps_and_valves_rk{index}_valve_opening",
        #     translation_key="valve_opening",
        #     translation_placeholders=valve_placeholders,
        #     device_component="pumps_and_valves",
        # ),
    )


_PUMPS_AND_VALVES_RK4: tuple[TrovisBinaryDescription, ...] = (
    _binary(
        "rk4",
        "storage_tank_charging_pump_running",
        "SLP storage tank charging pump",
        key="pumps_and_valves_slp",
        translation_key="storage_tank_charging_pump_running",
        translation_placeholders={"component": "SLP"},
        device_component="pumps_and_valves",
    ),
    _binary(
        "rk4",
        "circulation_pump_running",
        "ZP circulation pump",
        key="pumps_and_valves_zp",
        translation_key="circulation_pump_running",
        translation_placeholders={"component": "ZP"},
        device_component="pumps_and_valves",
    ),
)


_RK4: tuple[TrovisBinaryDescription, ...] = (
    # move to 'Pumps and valves', also represented by switch in Rk4
    # _binary(
    #     "rk4",
    #     "storage_tank_charging_pump_running",
    #     "Storage tank charging pump",
    #     None,  # BinarySensorDeviceClass.RUNNING,
    #     key="rk4_storage_tank_charging_pump_running",
    #     translation_key="storage_tank_charging_pump_running",
    #     translation_placeholders={"component": "Rk4"},
    # ),
    # _binary(
    #     "rk4",
    #     "circulation_pump_running",
    #     "Circulation pump",
    #     None,  # BinarySensorDeviceClass.RUNNING,
    #     key="rk4_circulation_pump_running",
    #     translation_key="circulation_pump_running",
    #     translation_placeholders={"component": "Rk4"},
    # ),
    _binary(
        "rk4",
        "disinfection_active",
        "Disinfection",
        BinarySensorDeviceClass.RUNNING,
        key="rk4_disinfection_active",
        translation_key="disinfection_active",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "manual_active",
        "Manual operation",
        key="rk4_manual_active",
        translation_key="manual_active",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "automatic",
        "Automatic operation",
        key="rk4_automatic",
        translation_key="automatic",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "priority",
        "Domestic hot-water priority",
        key="rk4_priority",
        translation_key="priority",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "maximum_charging_temperature_limit_active",
        "Maximum charging-temperature limit",
        key="rk4_maximum_charging_temperature_limit_active",
        translation_key="maximum_charging_temperature_limit_active",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "return_limit_active",
        "Return-temperature limit",
        key="rk4_return_limit_active",
        translation_key="return_limit_active",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "standby",
        "Standby",
        key="rk4_standby",
        translation_key="standby",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "frost_protection",
        "Frost protection",
        BinarySensorDeviceClass.COLD,
        key="rk4_frost_protection",
        translation_key="frost_protection",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "storage_tank_charging_active",
        "Storage charging active",
        BinarySensorDeviceClass.RUNNING,
        key="rk4_storage_tank_charging_active",
        translation_key="storage_tank_charging_active",
        translation_placeholders={"component": "Rk4"},
    ),
    _binary(
        "rk4",
        "storage_tank_charging_locked",
        "Storage charging locked",
        key="rk4_storage_tank_charging_locked",
        translation_key="storage_tank_charging_locked",
        translation_placeholders={"component": "Rk4"},
    ),
)


_SOLAR: tuple[TrovisBinaryDescription, ...] = (
    _binary(
        "solar",
        "pump_running",
        "Solar circuit pump",
        BinarySensorDeviceClass.RUNNING,
        key="solar_pump_running",
        translation_key="solar_pump_running",
    ),
)


_PUMPS_AND_VALVES_SOLAR: tuple[TrovisBinaryDescription, ...] = (
    _binary(
        "solar",
        "pump_running",
        "Solar circuit pump",
        key="pumps_and_valves_solar_pump",
        translation_key="solar_pump_running",
        device_component="pumps_and_valves",
    ),
)


def _description_supported(
    coordinator: TrovisCoordinator,
    description: TrovisBinaryDescription,
) -> bool:
    """Return whether one binary state applies to the resolved circuit role."""
    component = getattr(coordinator.device, description.component)
    if not component_supports_datapoint(component, description.field):
        return False

    if description.component in {"rk1", "rk2", "rk3"}:
        index = int(description.component[-1])
        if (
            description.field in _ROOM_HEATING_ONLY_BINARY_FIELDS
            and index not in coordinator.device.room_heating_circuit_indices
        ):
            return False

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Trovis binary sensors."""
    coordinator = entry.runtime_data
    descriptions = list(_CONTROLLER)
    if coordinator.device.has_rk4:
        descriptions.extend(_RK4)
        descriptions.extend(_PUMPS_AND_VALVES_RK4)
    if coordinator.device.has_solar:
        descriptions.extend(_SOLAR)
        descriptions.extend(_PUMPS_AND_VALVES_SOLAR)

    for index in rk1_to_rk3_indices(coordinator):
        component = f"rk{index}"
        placeholders = {"component": f"Rk{index}"}
        descriptions.extend(_pumps_and_valves_rk_binary_descriptions(index))
        descriptions.extend(
            _binary(
                component,
                field,
                f"Rk{index} - {name}",
                device_class,
                key=f"rk{index}_{key_suffix}",
                translation_key=field,
                translation_placeholders=placeholders,
                enabled=enabled,
            )
            for field, key_suffix, name, device_class, enabled in _CIRCUIT_STATES
        )

    async_add_entities(
        TrovisBinarySensor(coordinator, description)
        for description in descriptions
        if _description_supported(coordinator, description)
    )


class TrovisBinarySensor(TrovisEntity, BinarySensorEntity):
    """A single read-only boolean value."""

    entity_description: TrovisBinaryDescription

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        description: TrovisBinaryDescription,
    ) -> None:
        super().__init__(
            coordinator,
            description.key,
            description.component,
            "binary_sensor",
            translation_key=description.translation_key,
            translation_placeholders=description.translation_placeholders,
            device_component=description.device_component,
        )
        self.entity_description = description
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )

    @property
    def is_on(self) -> bool | None:
        """Return the current boolean state."""
        return getattr(self._subsystem, self.entity_description.field)
