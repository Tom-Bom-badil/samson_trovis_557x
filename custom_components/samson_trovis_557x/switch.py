"""Switch entities for writable TROVIS boolean values."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from trovis_modbus import TrovisWriteAccessError
from trovis_modbus.metadata import BooleanMetadata

from . import (
    TrovisEntity,
    component_supports_datapoint,
    require_boolean_metadata,
    rk1_to_rk3_indices,
)
from .coordinator import TrovisConfigEntry, TrovisCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class TrovisSwitchDescription(SwitchEntityDescription):
    """Describe a Trovis switch entity.

    Boolean semantics and writeability come from trovis-modbus. This
    description only selects the field and stores Home Assistant presentation
    values.
    """

    component: str
    field: str
    translation_placeholders: dict[str, str] | None = None
    device_component: str | None = None


def _switch(
    component: str,
    field: str,
    name: str,
    *,
    key: str | None = None,
    translation_key: str | None = None,
    translation_placeholders: dict[str, str] | None = None,
    enabled: bool = True,
    device_component: str | None = None,
) -> TrovisSwitchDescription:
    """Return a metadata-driven switch description."""
    return TrovisSwitchDescription(
        key=key or field,
        translation_key=translation_key,
        translation_placeholders=translation_placeholders,
        name=name,
        component=component,
        field=field,
        device_component=device_component,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=enabled,
    )


_CONTROLLER: tuple[TrovisSwitchDescription, ...] = (
    _switch(
        "controller",
        "delayed_outdoor_temperature_adaptation_falling",
        "Delayed outdoor-temperature adaptation (falling)",
    ),
    _switch(
        "controller",
        "delayed_outdoor_temperature_adaptation_rising",
        "Delayed outdoor-temperature adaptation (rising)",
    ),
    _switch(
        "controller",
        "automatic_summer_standard_time_switchover",
        "Automatic summer/standard time switchover",
        key="automatic_summer_standard_time_switchover",
        translation_key="automatic_summer_standard_time_switchover",
    ),
    _switch(
        "controller",
        "temperature_monitoring_enabled",
        "Temperature monitoring",
        key="temperature_monitoring_enabled",
        translation_key="temperature_monitoring_enabled",
    ),
    _switch(
        "controller",
        "manual_levels_locked",
        "Manual-operation levels locked",
    ),
    _switch(
        "controller",
        "rotary_switch_locked",
        "Rotary switches locked",
    ),
    _switch(
        "controller",
        "glt_timeout_active",
        "Supervisory-system timeout",
    ),
)


def _rk_switch_descriptions(index: int) -> tuple[TrovisSwitchDescription, ...]:
    """Return switch descriptions for one heating circuit."""
    component = f"rk{index}"
    prefix = f"rk{index}"
    placeholders = {"component": f"Rk{index}"}

    return (
        _switch(
            component,
            "three_point_control_enabled",
            f"Rk{index} 3-point control mode",
            key=f"{prefix}_control_parameter_mode",
            translation_key="control_parameter_mode",
            translation_placeholders=placeholders,
        ),
        _switch(
            component,
            "optimization",
            f"Rk{index} - Optimization",
            key=f"{prefix}_optimization",
            translation_key="optimization",
            translation_placeholders=placeholders,
        ),
        _switch(
            component,
            "adaptation",
            f"Rk{index} - Adaptation",
            key=f"{prefix}_adaptation",
            translation_key="adaptation",
            translation_placeholders=placeholders,
        ),
        _switch(
            component,
            "trovis_5570_room_control_unit",
            f"Rk{index} - TROVIS 5570 room control unit",
            key=f"{prefix}_room_control_unit",
            translation_key="trovis_5570_room_control_unit",
            translation_placeholders=placeholders,
        ),
        _switch(
            component,
            "pump_running",
            f"Rk{index} - Pump control",
            key=f"{prefix}_pump_control",
            translation_key="pump_control",
            translation_placeholders=placeholders,
        ),
    )


_RK4: tuple[TrovisSwitchDescription, ...] = (
    _switch(
        "rk4",
        "three_point_control_enabled",
        "Rk4 3-point control mode",
        key="rk4_control_parameter_mode",
        translation_key="control_parameter_mode",
        translation_placeholders={"component": "Rk4"},
    ),
    _switch(
        "rk4",
        "disinfection_enabled",
        "Rk4 - Thermal disinfection",
        key="rk4_disinfection_enabled",
        translation_key="disinfection_enabled",
        translation_placeholders={"component": "Rk4"},
    ),
    _switch(
        "rk4",
        "storage_tank_charging_pump_running",
        "Rk4 storage-tank-charging-pump control",
        key="rk4_storage_tank_charging_pump_control",
        translation_key="storage_tank_charging_pump_control",
        translation_placeholders={"component": "Rk4"},
    ),
    _switch(
        "rk4",
        "circulation_pump_running",
        "Rk4 circulation-pump control",
        key="rk4_circulation_pump_control",
        translation_key="circulation_pump_control",
        translation_placeholders={"component": "Rk4"},
    ),
    # ToDo - this looks like a redundant function ??? CL1831 ./. CO4-F07 + CL407
    # this is CL1831:
    # _switch(
    #     "rk4",
    #     "intermediate_heating_operation",
    #     "Rk4 intermediate heating operation",
    #     key="rk4_intermediate_heating_operation",
    #     translation_key="intermediate_heating_operation",
    #     translation_placeholders={"component": "Rk4"},
    # ),
    # this is CO4-F07 + CL407:
    _switch(
        "rk4",
        "intermediate_heating_function_enabled",
        "Rk4 intermediate heating function",
        key="rk4_intermediate_heating_function_enabled",
        translation_key="intermediate_heating_function_enabled",
        translation_placeholders={"component": "Rk4"},
    ),
    _switch(
        "rk4",
        "forced_charging",
        "Rk4 forced charging",
        key="rk4_forced_charging",
        translation_key="forced_charging",
        translation_placeholders={"component": "Rk4"},
    ),
    _switch(
        "rk4",
        "forced_charging_uses_storage_tank_sensor_2",
        "Rk4 forced charging using storage tank sensor 2",
        key="rk4_forced_charging_uses_storage_tank_sensor_2",
        translation_key="forced_charging_uses_storage_tank_sensor_2",
        translation_placeholders={"component": "Rk4"},
    ),
    _switch(
        "rk4",
        "storage_tank_charging_enabled",
        "Rk4 storage tank charging enabled",
        key="rk4_storage_tank_charging_enabled",
        translation_key="storage_tank_charging_enabled",
        translation_placeholders={"component": "Rk4"},
    ),
)


def _switch_description_supported(
    coordinator: TrovisCoordinator,
    description: TrovisSwitchDescription,
) -> bool:
    """Return whether one switch applies to the current controller setup."""
    component = getattr(coordinator.device, description.component)

    if not component_supports_datapoint(component, description.field):
        return False

    if description.field == "three_point_control_enabled":
        index = int(description.component.removeprefix("rk"))
        # Only offer F12 as a writable switch where both states are actually
        # supported. On systems with fixed three-point/continuous control, an
        # OFF write would otherwise expose an invalid two-point configuration.
        return coordinator.device.two_point_control_parameters_available(index)

    if (
        description.component == "rk4"
        and description.field == "intermediate_heating_function_enabled"
    ):
        return coordinator.device.intermediate_heating_available

    if description.component not in {"rk1", "rk2", "rk3"}:
        return True

    index = int(description.component[-1])

    if description.field == "optimization":
        return coordinator.device.heating_circuit_optimization_available(index)

    if description.field == "adaptation":
        return coordinator.device.heating_circuit_adaptation_available(index)

    if description.field == "trovis_5570_room_control_unit":
        return coordinator.device.trovis_5570_room_control_unit_available(index)

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Trovis switch entities."""
    coordinator = entry.runtime_data

    entities: list[SwitchEntity] = [TrovisWriteAccessSwitch(coordinator)]
    descriptions = list(_CONTROLLER)

    for index in rk1_to_rk3_indices(coordinator):
        descriptions.extend(_rk_switch_descriptions(index))

    if coordinator.device.has_rk4:
        descriptions.extend(_RK4)
    entities.extend(
        TrovisSwitch(coordinator, description)
        for description in descriptions
        if _switch_description_supported(coordinator, description)
    )

    async_add_entities(entities)


class TrovisWriteAccessSwitch(TrovisEntity, SwitchEntity):
    """Root switch that enables or disables TROVIS write access."""

    _attr_icon = "mdi:pencil-lock"

    def __init__(self, coordinator: TrovisCoordinator) -> None:
        super().__init__(
            coordinator,
            "write_access",
            "controller",
            "switch",
            translation_key="write_access",
        )

    @property
    def is_on(self) -> bool | None:
        """Return whether TROVIS writing is enabled."""
        return self.coordinator.device.writing_enabled

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable TROVIS writing."""
        try:
            await self.coordinator.device.async_enable_writing(
                access_code=self.coordinator.access_code,
            )
        except TrovisWriteAccessError as err:
            raise HomeAssistantError(str(err)) from err

        self.coordinator.async_set_updated_data(self.coordinator.device)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable TROVIS writing."""
        try:
            await self.coordinator.device.async_disable_writing()
        except TrovisWriteAccessError as err:
            _LOGGER.debug(
                "Controller rejected resetting TROVIS write access; "
                "disabling the HA write gate only",
                exc_info=err,
            )

        self.coordinator.async_set_updated_data(self.coordinator.device)


class TrovisSwitch(TrovisEntity, SwitchEntity):
    """Trovis switch entity."""

    entity_description: TrovisSwitchDescription

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        description: TrovisSwitchDescription,
    ) -> None:
        super().__init__(
            coordinator,
            description.key,
            description.component,
            "switch",
            translation_key=description.translation_key,
            translation_placeholders=description.translation_placeholders,
            device_component=description.device_component,
        )
        self.entity_description = description
        self._boolean_metadata: BooleanMetadata = require_boolean_metadata(
            self._subsystem,
            description.field,
        )
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )

    def _to_ha_bool(self, value: bool) -> bool:
        """Convert the controller value to Home Assistant switch semantics."""
        result = bool(value)
        if self._boolean_metadata.inverted:
            return not result
        return result

    def _from_ha_bool(self, value: bool) -> bool:
        """Convert Home Assistant switch semantics to controller value."""
        if self._boolean_metadata.inverted:
            return not value
        return value

    @property
    def is_on(self) -> bool | None:
        """Return whether the switch is on."""
        value = getattr(self._subsystem, self.entity_description.field)
        if value is None:
            return None

        return self._to_ha_bool(bool(value))

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the switch on."""
        await self._async_set_switch(self._from_ha_bool(True))

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the switch off."""
        await self._async_set_switch(self._from_ha_bool(False))

    async def _async_set_switch(self, value: bool) -> None:
        """Set the switch state through the shared library write path."""
        await self._async_write_datapoint(self.entity_description.field, value)
