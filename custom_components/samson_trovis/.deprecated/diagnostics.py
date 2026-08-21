"""Diagnostics support for SAMSON TROVIS."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .constants.config import CONF_PORT_URL

TO_REDACT = {CONF_PORT_URL}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return {
        "entry": {
            "data": {key: ("**REDACTED**" if key in TO_REDACT else value) for key, value in entry.data.items()},
            "options": dict(entry.options),
        }
    }
