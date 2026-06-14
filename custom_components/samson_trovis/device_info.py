"""Device info helpers for SAMSON TROVIS."""

from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from .constants.config import CONF_MODEL, DOMAIN, MANUFACTURER


def get_device_info(entry: ConfigEntry) -> dict:
    """Return Home Assistant device info for a TROVIS controller."""
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "manufacturer": MANUFACTURER,
        "model": entry.data.get(CONF_MODEL),
        "name": entry.title,
    }
