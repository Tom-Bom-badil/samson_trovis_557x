"""Data update coordinator for SAMSON TROVIS."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo

from .device_info import get_device_info
from .api import TrovisApi
from .constants.config import DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN


_LOGGER = logging.getLogger(__name__)


class TrovisDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate TROVIS data updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: TrovisApi) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this config entry."""
        return get_device_info(self.entry)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the TROVIS controller."""
        return await self.api.async_read_enabled_areas()
