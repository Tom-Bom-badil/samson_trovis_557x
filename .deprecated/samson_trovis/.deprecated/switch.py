"""Switch platform for SAMSON TROVIS."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TrovisConfigEntry
from .constants.areas import DEFAULT_ENABLED_AREAS
from .constants.config import CONF_ENABLED_AREAS, CONF_SLUG
from .constants.coils import ALL_COILS
from .constants.descriptions import TrovisCoilDescription
from .entities import TrovisEntity


_LOGGER = logging.getLogger(__name__)


class TrovisCoilSwitch(TrovisEntity, SwitchEntity):
    """Representation of a writable TROVIS coil."""

    entity_description: TrovisCoilDescription

    @property
    def is_on(self) -> bool | None:
        """Return whether the switch is on."""
        value = self.coordinator.data.get(self.entity_description.key)

        if value is None:
            return None

        return bool(value)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._async_set_state(False)

    async def _async_set_state(self, value: bool) -> None:
        """Set the coil state."""
        success = await self.coordinator.api.async_write_coil_description(
            self.entity_description,
            value,
        )

        if not success:
            _LOGGER.warning(
                "Failed to write TROVIS switch entity %s with value %s",
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
    """Set up SAMSON TROVIS switch entities."""
    coordinator = entry.runtime_data.coordinator
    enabled_areas = set(entry.options.get(CONF_ENABLED_AREAS) or DEFAULT_ENABLED_AREAS)
    entity_slug = entry.data.get(CONF_SLUG, entry.title)

    entities = [
        TrovisCoilSwitch(coordinator, description)
        for description in ALL_COILS
        if description.platform == Platform.SWITCH
        and description.area in enabled_areas
        and not description.read_only
    ]

    _LOGGER.info(
        "Setting up %s SAMSON TROVIS switch entities for %s: enabled_areas=%s all_coils=%s",
        len(entities),
        entity_slug,
        sorted(enabled_areas),
        len(ALL_COILS),
    )

    async_add_entities(entities)