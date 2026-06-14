"""Binary sensor platform for SAMSON TROVIS."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TrovisConfigEntry
from .constants.areas import DEFAULT_ENABLED_AREAS
from .constants.coils import ALL_COILS
from .constants.config import CONF_ENABLED_AREAS
from .constants.descriptions import TrovisCoilDescription
from .entities import TrovisEntity

_LOGGER = logging.getLogger(__name__)


class TrovisCoilBinarySensor(TrovisEntity, BinarySensorEntity):
    """Representation of a TROVIS coil binary sensor."""

    entity_description: TrovisCoilDescription

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        value = self.coordinator.data.get(self.entity_description.key)

        if value is None:
            return None

        return bool(value)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAMSON TROVIS binary sensor entities."""
    coordinator = entry.runtime_data.coordinator
    enabled_areas = set(entry.options.get(CONF_ENABLED_AREAS) or DEFAULT_ENABLED_AREAS)

    entities = [
        TrovisCoilBinarySensor(coordinator, description)
        for description in ALL_COILS
        if description.platform == Platform.BINARY_SENSOR and description.area in enabled_areas
    ]

    _LOGGER.info(
        "Setting up %s SAMSON TROVIS binary sensor entities: enabled_areas=%s all_coils=%s",
        len(entities),
        sorted(enabled_areas),
        len(ALL_COILS),
    )

    async_add_entities(entities)