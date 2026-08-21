"""SAMSON TROVIS integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import TrovisApi
from .constants.config import PLATFORMS
from .coordinator import TrovisDataUpdateCoordinator
from .transport import TrovisTransport


@dataclass
class TrovisRuntimeData:
    """Runtime data for one TROVIS config entry."""

    transport: TrovisTransport
    api: TrovisApi
    coordinator: TrovisDataUpdateCoordinator


type TrovisConfigEntry = ConfigEntry[TrovisRuntimeData]


# Import platforms at module level so Home Assistant does not lazy-import them
# inside the event loop during async_forward_entry_setups().
from . import binary_sensor as _binary_sensor  # noqa: F401,E402
from . import number as _number  # noqa: F401,E402
from . import select as _select  # noqa: F401,E402
from . import sensor as _sensor  # noqa: F401,E402
from . import switch as _switch  # noqa: F401,E402


async def async_setup_entry(hass: HomeAssistant, entry: TrovisConfigEntry) -> bool:
    """Set up SAMSON TROVIS from a config entry."""
    transport = TrovisTransport(hass, entry)
    api = TrovisApi(transport, entry)
    coordinator = TrovisDataUpdateCoordinator(hass, entry, api)

    entry.runtime_data = TrovisRuntimeData(
        transport=transport,
        api=api,
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TrovisConfigEntry) -> bool:
    """Unload a SAMSON TROVIS config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await entry.runtime_data.transport.async_close()

    return unload_ok
