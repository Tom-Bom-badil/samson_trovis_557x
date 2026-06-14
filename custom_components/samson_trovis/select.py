"""Select platform for SAMSON TROVIS."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TrovisConfigEntry
from .constants.areas import DEFAULT_ENABLED_AREAS
from .constants.config import CONF_ENABLED_AREAS
from .constants.descriptions import TrovisRegisterDescription
from .constants.registers import ALL_REGISTERS
from .entities import TrovisEntity


_LOGGER = logging.getLogger(__name__)


class TrovisRegisterSelect(TrovisEntity, SelectEntity):
    """Representation of a writable TROVIS enum register."""

    entity_description: TrovisRegisterDescription

    def __init__(
        self,
        coordinator,
        description: TrovisRegisterDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, description)
        self._attr_options = [str(option) for option in (description.enum_map or {}).values()]

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        value = self.coordinator.data.get(self.entity_description.key)

        if value is None:
            return None

        option = str(value)
        if option not in self.options:
            return None

        return option

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        success = await self.coordinator.api.async_write_register_option(
            self.entity_description,
            option,
        )

        if not success:
            _LOGGER.warning(
                "Failed to write TROVIS select entity %s with option %s",
                self.entity_description.key,
                option,
            )
            return

        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAMSON TROVIS select entities."""
    coordinator = entry.runtime_data.coordinator
    enabled_areas = set(entry.options.get(CONF_ENABLED_AREAS) or DEFAULT_ENABLED_AREAS)

    entities = [
        TrovisRegisterSelect(coordinator, description)
        for description in ALL_REGISTERS
        if description.platform == Platform.SELECT
        and description.area in enabled_areas
        and not description.read_only
        and description.enum_map
    ]

    _LOGGER.info(
        "Setting up %s SAMSON TROVIS select entities: enabled_areas=%s all_registers=%s",
        len(entities),
        sorted(enabled_areas),
        len(ALL_REGISTERS),
    )

    async_add_entities(entities)