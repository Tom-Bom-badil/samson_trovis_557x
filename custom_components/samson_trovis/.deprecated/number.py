"""Number platform for SAMSON TROVIS."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TrovisConfigEntry
from .constants.areas import DEFAULT_ENABLED_AREAS
from .constants.config import CONF_ENABLED_AREAS, CONF_SLUG
from .constants.descriptions import TrovisRegisterDescription
from .constants.registers import ALL_REGISTERS
from .entities import TrovisEntity


_LOGGER = logging.getLogger(__name__)


class TrovisRegisterNumber(TrovisEntity, NumberEntity):
    """Representation of a writable TROVIS register."""

    entity_description: TrovisRegisterDescription

    def __init__(
        self,
        coordinator,
        description: TrovisRegisterDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, description)
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_class = description.device_class
        self._attr_mode = NumberMode.BOX

    async def async_set_native_value(self, value: float) -> None:
        """Set the native value."""
        success = await self.coordinator.api.async_write_register_description(
            self.entity_description,
            value,
        )

        if not success:
            _LOGGER.warning(
                "Failed to write TROVIS number entity %s with value %s",
                self.entity_description.key,
                value,
            )
            return

        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAMSON TROVIS number entities."""
    coordinator = entry.runtime_data.coordinator
    enabled_areas = set(entry.options.get(CONF_ENABLED_AREAS) or DEFAULT_ENABLED_AREAS)
    entity_slug = entry.data.get(CONF_SLUG, entry.title)

    entities = [
        TrovisRegisterNumber(coordinator, description)
        for description in ALL_REGISTERS
        if description.platform == Platform.NUMBER
        and description.area in enabled_areas
        and not description.read_only
    ]

    _LOGGER.info(
        "Setting up %s SAMSON TROVIS number entities for %s: enabled_areas=%s all_registers=%s",
        len(entities),
        entity_slug,
        sorted(enabled_areas),
        len(ALL_REGISTERS),
    )

    async_add_entities(entities)