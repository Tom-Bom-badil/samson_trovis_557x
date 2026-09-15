"""Date entities for TROVIS controller values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from homeassistant.components.date import DateEntity, DateEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from trovis_modbus import MonthDay

from . import TrovisEntity
from .coordinator import TrovisConfigEntry, TrovisCoordinator

DateValueKind = Literal["date", "month_day"]


@dataclass(frozen=True, kw_only=True)
class TrovisDateDescription(DateEntityDescription):
    """Description of a native TROVIS date entity."""

    component: str
    field: str
    value_kind: DateValueKind = "date"


_DATES: tuple[TrovisDateDescription, ...] = (
    TrovisDateDescription(
        key="controller_date",
        translation_key="controller_date",
        name="Controller date",
        component="clock",
        field="date",
        entity_category=EntityCategory.CONFIG,
    ),
    TrovisDateDescription(
        key="summer_start",
        translation_key="summer_start",
        name="Summer period start",
        component="controller",
        field="summer_start",
        value_kind="month_day",
        entity_category=EntityCategory.CONFIG,
    ),
    TrovisDateDescription(
        key="summer_end",
        translation_key="summer_end",
        name="Summer period end",
        component="controller",
        field="summer_end",
        value_kind="month_day",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up native TROVIS date entities."""
    async_add_entities(
        TrovisDate(entry.runtime_data, description) for description in _DATES
    )


class TrovisDate(TrovisEntity, DateEntity):
    """A native date backed by one trovis-modbus datapoint."""

    entity_description: TrovisDateDescription

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        description: TrovisDateDescription,
    ) -> None:
        super().__init__(
            coordinator,
            description.key,
            description.component,
            "date",
            translation_key=description.translation_key,
        )
        self.entity_description = description
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )

    @property
    def native_value(self) -> date | None:
        """Return the date in Home Assistant form."""
        value = getattr(self._subsystem, self.entity_description.field)

        if value is None:
            return None

        if self.entity_description.value_kind == "month_day":
            if not isinstance(value, MonthDay):
                return None

            year = self.coordinator.device.clock.year
            if year is None:
                return None

            try:
                return date(year, value.month, value.day)
            except ValueError:
                return None

        return value

    async def async_set_value(self, value: date) -> None:
        """Set the date through the shared library write path."""
        if self.entity_description.value_kind == "month_day":
            await self._async_write_datapoint(
                self.entity_description.field,
                MonthDay(day=value.day, month=value.month),
            )
            return

        await self._async_write_datapoint(
            self.entity_description.field,
            value,
        )
