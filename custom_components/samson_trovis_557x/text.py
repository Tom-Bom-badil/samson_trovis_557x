"""Text entities for per-controller Modbus read exclusions."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.text import TextEntity, TextEntityDescription, TextMode
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TrovisEntity
from .const import CONF_EXCLUDED_COILS, CONF_EXCLUDED_REGISTERS
from .coordinator import TrovisConfigEntry, TrovisCoordinator
from .exclusion_state import CONF_AUTO_EXCLUSIONS_FIRMWARE, option_parts, with_manual
from .read_exclusions import (
    ADDRESS_LIST_PATTERN,
    normalize_address_list,
    parse_address_list,
)


@dataclass(frozen=True, kw_only=True)
class TrovisReadExclusionTextDescription(TextEntityDescription):
    """Describe one local Modbus read-exclusion setting."""

    option_key: str


_TEXTS: tuple[TrovisReadExclusionTextDescription, ...] = (
    TrovisReadExclusionTextDescription(
        key="excluded_registers",
        name="Excluded registers (0-based)",
        option_key=CONF_EXCLUDED_REGISTERS,
        native_min=0,
        native_max=255,
        mode=TextMode.TEXT,
        pattern=ADDRESS_LIST_PATTERN,
        entity_category=EntityCategory.CONFIG,
    ),
    TrovisReadExclusionTextDescription(
        key="excluded_coils",
        name="Excluded coils (0-based)",
        option_key=CONF_EXCLUDED_COILS,
        native_min=0,
        native_max=255,
        mode=TextMode.TEXT,
        pattern=ADDRESS_LIST_PATTERN,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up per-controller Modbus read-exclusion text entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        TrovisReadExclusionText(coordinator, description) for description in _TEXTS
    )


class TrovisReadExclusionText(TrovisEntity, TextEntity):
    """Manual input as state; automatically confirmed exclusions as attributes."""

    entity_description: TrovisReadExclusionTextDescription

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        description: TrovisReadExclusionTextDescription,
    ) -> None:
        super().__init__(
            coordinator,
            description.key,
            "controller",
            "text",
            translation_key=description.key,
        )
        self.entity_description = description
        self._value, _ = option_parts(
            coordinator.config_entry.options.get(description.option_key)
        )

    @property
    def available(self) -> bool:
        """Keep manual exclusions editable even if controller polling fails."""
        return True

    @property
    def native_value(self) -> str:
        """Return exclusively the manually entered list."""
        return self._value

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Present automatic exclusions without storing them as HA state."""
        _, automatic = option_parts(
            self.coordinator.config_entry.options.get(
                self.entity_description.option_key
            )
        )
        reference = self.coordinator.config_entry.options.get(
            CONF_AUTO_EXCLUSIONS_FIRMWARE
        )
        firmware_label = (
            f"{reference // 100}.{reference % 100:02d}"
            if isinstance(reference, int) and not isinstance(reference, bool)
            else None
        )
        return {
            "auto_excluded": automatic,
            "auto_count": len(parse_address_list(automatic)),
            "auto_firmware": firmware_label,
        }

    async def async_set_value(self, value: str) -> None:
        """Update the manual portion only and reload the config entry."""
        try:
            normalized = normalize_address_list(value)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

        if normalized == self._value:
            return
        entry = self.coordinator.config_entry
        try:
            options = with_manual(
                entry.options,
                self.entity_description.option_key,
                normalized,
            )
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err
        self._value = normalized
        self.async_write_ha_state()
        if self.hass.config_entries.async_update_entry(entry, options=options):
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
