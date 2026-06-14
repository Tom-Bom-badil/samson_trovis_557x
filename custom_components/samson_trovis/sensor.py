"""sensor platform for SAMSON TROVIS."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TrovisConfigEntry
from .constants.areas import DEFAULT_ENABLED_AREAS
from .constants.config import CONF_ENABLED_AREAS
from .constants.descriptions import TrovisRegisterDescription
from .constants.registers import ALL_REGISTERS
from .entities import TrovisEntity


class TrovisRegisterSensor(TrovisEntity, SensorEntity):
    """Representation of a TROVIS register sensor."""

    entity_description: TrovisRegisterDescription

    def __init__(
        self,
        coordinator,
        description: TrovisRegisterDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAMSON TROVIS sensor entities."""
    coordinator = entry.runtime_data.coordinator
    enabled_areas = set(entry.options.get(CONF_ENABLED_AREAS) or DEFAULT_ENABLED_AREAS)

    entities = [
        TrovisRegisterSensor(coordinator, description)
        for description in ALL_REGISTERS
        if description.platform == Platform.SENSOR and description.area in enabled_areas
    ]

    async_add_entities(entities)