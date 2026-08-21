"""Device info helpers for SAMSON TROVIS."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .constants.areas import AREA_DEVICE_TRANSLATION_KEYS, ROOT_DEVICE_AREAS
from .constants.config import CONF_MODEL, DOMAIN, MANUFACTURER


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return Home Assistant device info for a TROVIS controller."""
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "manufacturer": MANUFACTURER,
        "model": entry.data.get(CONF_MODEL),
        "name": entry.title,
    }


def get_area_device_info(entry: ConfigEntry, area: str) -> DeviceInfo:
    """Return Home Assistant device info for a TROVIS functional area."""
    if area in ROOT_DEVICE_AREAS:
        return get_device_info(entry)

    translation_key = AREA_DEVICE_TRANSLATION_KEYS.get(area)

    device_info: DeviceInfo = {
        "identifiers": {(DOMAIN, f"{entry.entry_id}_{area}")},
        "manufacturer": MANUFACTURER,
        "model": entry.data.get(CONF_MODEL),
        "via_device": (DOMAIN, entry.entry_id),
    }

    if translation_key is not None:
        device_info["translation_key"] = translation_key
    else:
        device_info["name"] = area.replace("_", " ").title()

    return device_info