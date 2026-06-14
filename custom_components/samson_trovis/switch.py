"""switch platform for SAMSON TROVIS."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TrovisConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAMSON TROVIS switch entities."""
    # TODO: Build entities from constants/registers and constants/coils.
    async_add_entities([])
