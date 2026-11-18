"""Controller-local maintenance action for auto-learned read exclusions."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TrovisEntity
from .coordinator import TrovisConfigEntry, TrovisCoordinator
from .exclusion_state import clear_automatic

_START_STOP_SCAN = ButtonEntityDescription(
    key="datapoint_scan",
    name="ZZ - Sniffer Start / Stop (takes time!)",
    entity_category=EntityCategory.DIAGNOSTIC,
)


_RESET_AUTOMATIC = ButtonEntityDescription(
    key="clear_auto_exclusions",
    name="Reset automatically excluded Modbus addresses",
    entity_category=EntityCategory.CONFIG,
    entity_registry_enabled_default=False,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a disabled-by-default, local-only reset button."""
    async_add_entities(
        [
            TrovisResetAutoExclusionsButton(entry.runtime_data),
            TrovisDatapointScanButton(entry.runtime_data),
        ]
    )


class TrovisResetAutoExclusionsButton(TrovisEntity, ButtonEntity):
    """Forget auto-learned exclusions; never write anything over Modbus."""

    def __init__(self, coordinator: TrovisCoordinator) -> None:
        super().__init__(
            coordinator,
            _RESET_AUTOMATIC.key,
            "controller",
            "button",
            translation_key=_RESET_AUTOMATIC.key,
        )
        self.entity_description = _RESET_AUTOMATIC

    @property
    def available(self) -> bool:
        """Keep recovery/reset available even when polling has failed."""
        return True

    async def async_press(self) -> None:
        """Drop only the learned part and reload to rebuild the read plan."""
        if self.coordinator.scan_active:
            return
        entry = self.coordinator.config_entry
        updated = clear_automatic(entry.options)
        if updated != dict(entry.options):
            if self.hass.config_entries.async_update_entry(entry, options=updated):
                self.hass.config_entries.async_schedule_reload(entry.entry_id)


class TrovisDatapointScanButton(TrovisEntity, ButtonEntity):
    """Toggle one controller-local read-only address scan."""

    def __init__(self, coordinator: TrovisCoordinator) -> None:
        super().__init__(
            coordinator,
            _START_STOP_SCAN.key,
            "controller",
            "button",
            translation_key=_START_STOP_SCAN.key,
        )
        self.entity_description = _START_STOP_SCAN

    @property
    def available(self) -> bool:
        """Allow cancellation even if the normal polling coordinator failed."""
        return True

    async def async_press(self) -> None:
        """Return immediately; the coordinator manages the background task."""
        self.coordinator.async_toggle_scan()
