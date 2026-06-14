"""Shared entity helpers for SAMSON TROVIS."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import async_generate_entity_id

from .constants.config import CONF_SLUG
from .constants.descriptions import TrovisEntityDescription
from .coordinator import TrovisDataUpdateCoordinator


class TrovisEntity(CoordinatorEntity[TrovisDataUpdateCoordinator]):
    """Base class for SAMSON TROVIS entities."""

    entity_description: TrovisEntityDescription

    def __init__(
        self,
        coordinator: TrovisDataUpdateCoordinator,
        description: TrovisEntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        entity_slug = coordinator.entry.data[CONF_SLUG]
        entity_key = description.key
        entity_domain = description.platform.value

        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{entity_key}"
        self._attr_translation_key = entity_key
        self._attr_has_entity_name = True
        self._attr_device_info = coordinator.device_info
        self._attr_suggested_object_id = f"{entity_slug}_{entity_key}"

        self.entity_id = async_generate_entity_id(
            f"{entity_domain}.{{}}",
            f"{entity_slug}_{entity_key}",
            hass=coordinator.hass,
        )


    @property
    def native_value(self) -> Any:
        """Return the native value."""
        return self.coordinator.data.get(self.entity_description.key)
