"""DataUpdateCoordinator that polls the Trovis controller."""

from __future__ import annotations

import logging
from time import monotonic

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from modbus_connection import ModbusError
from trovis_modbus import DEFAULT_WRITE_ACCESS_CODE, Trovis557x
from trovis_modbus.utils import (
    async_confirm_illegal_addresses,
    illegal_address_block,
)

from .const import (
    CONF_ACCESS_CODE,
    CONF_EXCLUDED_COILS,
    CONF_EXCLUDED_REGISTERS,
    DOMAIN,
    SCAN_INTERVAL,
)
from .exclusion_state import (
    CONF_AUTO_EXCLUSIONS_FIRMWARE,
    option_parts,
    with_confirmed_automatic,
)
from .read_exclusions import parse_address_list

_LOGGER = logging.getLogger(__name__)
_DEV_LOGGER = logging.getLogger("TROVIS dev log")

type TrovisConfigEntry = ConfigEntry["TrovisCoordinator"]


class TrovisCoordinator(DataUpdateCoordinator[Trovis557x]):
    """Poll a TROVIS controller through its Modbus unit."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: TrovisConfigEntry,
        device: Trovis557x,
        *,
        developer_mode: bool = False,
    ) -> None:
        """Initialize the TROVIS coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=SCAN_INTERVAL,
        )

        self.device = device
        self._developer_mode = developer_mode
        self._exclusion_reload_pending = False

        if developer_mode:
            _DEV_LOGGER.setLevel(logging.INFO)

    @property
    def access_code(self) -> int:
        """Return the configured TROVIS write access code."""
        return int(
            self.config_entry.data.get(
                CONF_ACCESS_CODE,
                DEFAULT_WRITE_ACCESS_CODE,
            )
        )

    async def _async_update_data(self) -> Trovis557x:
        """Refresh all TROVIS data."""
        started = monotonic()

        try:
            await self.device.async_update()
        except ModbusError as err:
            await self._async_diagnose_illegal_address(err)
            if self._developer_mode:
                _DEV_LOGGER.info(
                    "%s: Full read failed after %.2fs.",
                    self.config_entry.title,
                    monotonic() - started,
                )

            raise UpdateFailed(f"Error communicating with Trovis: {err}") from err

        if self._developer_mode:
            _DEV_LOGGER.info(
                "%s: Full read took %.2fs.",
                self.config_entry.title,
                monotonic() - started,
            )

        return self.device

    async def _async_diagnose_illegal_address(self, error: ModbusError) -> None:
        """Learn only confirmed single-address 0x02 errors from bounded blocks."""
        if self._exclusion_reload_pending:
            return
        block = illegal_address_block(error)
        firmware = getattr(self.device, "firmware_reference", None)
        if block is None or not isinstance(firmware, int):
            return
        entry = self.config_entry
        key = (
            CONF_EXCLUDED_REGISTERS if block.space == "holding" else CONF_EXCLUDED_COILS
        )
        try:
            confirmed = await async_confirm_illegal_addresses(self.device._unit, block)
        except ModbusError as diagnostic_error:
            _LOGGER.warning(
                "%s: Cannot confirm illegal %s block %d..%d: %s; "
                "no automatic exclusion learned",
                entry.title,
                block.space,
                block.address,
                block.address + block.count - 1,
                diagnostic_error,
            )
            return
        if not confirmed:
            _LOGGER.warning(
                "%s: Read block %s %d..%d was rejected with 0x02, "
                "but every single address succeeded; no exclusion learned",
                entry.title,
                block.space,
                block.address,
                block.address + block.count - 1,
            )
            return
        try:
            manually, automatically = option_parts(entry.options.get(key))
            firmware_matches = (
                entry.options.get(CONF_AUTO_EXCLUSIONS_FIRMWARE) == firmware
            )
            already_excluded = parse_address_list(manually) | (
                parse_address_list(automatically) if firmware_matches else frozenset()
            )
            to_add = confirmed - already_excluded
            if not to_add:
                return
            options = with_confirmed_automatic(
                entry.options,
                firmware,
                set(to_add) if block.space == "holding" else set(),
                set(to_add) if block.space == "coil" else set(),
            )
        except ValueError as err:
            _LOGGER.error(
                "%s: Cannot persist automatic Modbus exclusions: %s",
                entry.title,
                err,
            )
            return
        _LOGGER.warning(
            "%s: Model %s / firmware %d: confirmed Modbus 0x02 for %s "
            "block %d..%d; excluding only addresses %s (zero-based)",
            entry.title,
            self.device.model,
            firmware,
            block.space,
            block.address,
            block.address + block.count - 1,
            ",".join(str(address) for address in sorted(to_add)),
        )
        if self.hass.config_entries.async_update_entry(entry, options=options):
            self._exclusion_reload_pending = True
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
