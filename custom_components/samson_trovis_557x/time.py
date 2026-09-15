"""Time entities for TROVIS controller values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TrovisEntity
from .coordinator import TrovisConfigEntry, TrovisCoordinator


@dataclass(frozen=True, kw_only=True)
class TrovisTimeDescription(TimeEntityDescription):
    """Description of a native TROVIS time entity."""

    component: str
    field: str
    translation_placeholders: dict[str, str] | None = None


_TIMES: tuple[TrovisTimeDescription, ...] = (
    TrovisTimeDescription(
        key="controller_time",
        translation_key="controller_time",
        name="Controller time",
        component="clock",
        field="time",
        entity_category=EntityCategory.CONFIG,
    ),
    TrovisTimeDescription(
        key="rk4_disinfection_start",
        translation_key="disinfection_start",
        name="Rk4 disinfection start",
        component="rk4",
        field="disinfection_start",
        entity_category=EntityCategory.CONFIG,
        translation_placeholders={"component": "Rk4"},
    ),
    TrovisTimeDescription(
        key="rk4_disinfection_stop",
        translation_key="disinfection_stop",
        name="Rk4 disinfection end",
        component="rk4",
        field="disinfection_stop",
        entity_category=EntityCategory.CONFIG,
        translation_placeholders={"component": "Rk4"},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up native TROVIS time entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        TrovisTime(coordinator, description)
        for description in _TIMES
        if description.component != "rk4" or coordinator.device.has_rk4
    )


class TrovisTime(TrovisEntity, TimeEntity):
    """A native time backed by one trovis-modbus datapoint."""

    entity_description: TrovisTimeDescription

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        description: TrovisTimeDescription,
    ) -> None:
        super().__init__(
            coordinator,
            description.key,
            description.component,
            "time",
            translation_key=description.translation_key,
            translation_placeholders=description.translation_placeholders,
        )
        self.entity_description = description
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )

    @property
    def native_value(self) -> time | None:
        """Return the native controller time."""
        return getattr(self._subsystem, self.entity_description.field)

    async def async_set_value(self, value: time) -> None:
        """Set a controller time through the shared library write path."""
        await self._async_write_datapoint(self.entity_description.field, value)
