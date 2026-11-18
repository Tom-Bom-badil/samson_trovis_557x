"""DataUpdateCoordinator that polls the Trovis controller."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from time import monotonic

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from modbus_connection import ModbusError
from trovis_modbus import (
    DEFAULT_WRITE_ACCESS_CODE,
    ScanProgress,
    Trovis557x,
    async_scan_datapoints,
)
from trovis_modbus.sniffer import COIL_COUNT, REGISTER_COUNT
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
        self._modbus_lock = asyncio.Lock()
        self._scan_active = False
        self._scan_task: asyncio.Task[None] | None = None
        self._scan_listener: Callable[[], None] | None = None
        self._scan_last_progress = 0
        self._scan_last_phase: str | None = None
        self._scan_unloading = False
        self.scan_status = "Idle"
        self.scan_report: str | None = None
        self.scan_timestamp: str | None = None
        self.scan_requests = 0

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

    @property
    def scan_active(self) -> bool:
        """Whether the controller is reserved for its read-only address scan."""
        return self._scan_active

    def register_scan_listener(
        self, listener: Callable[[], None]
    ) -> Callable[[], None]:
        """Publish scan state only to the scan entity, not all TROVIS entities."""
        self._scan_listener = listener

        def unsubscribe() -> None:
            if self._scan_listener is listener:
                self._scan_listener = None

        return unsubscribe

    def _notify_scan(self) -> None:
        if self._scan_listener is not None:
            self._scan_listener()

    @asynccontextmanager
    async def async_modbus_write_guard(self) -> AsyncIterator[None]:
        """Never allow HA-originated Modbus writes to overlap a scan/poll."""
        if self._scan_active:
            raise HomeAssistantError(
                "TROVIS datapoint scan is running; writing is paused"
            )
        async with self._modbus_lock:
            if self._scan_active:
                raise HomeAssistantError(
                "TROVIS datapoint scan is running; writing is paused"
            )
            yield

    def async_toggle_scan(self) -> None:
        """Start a fresh scan or request cancellation of the running scan."""
        if self._scan_task is not None and not self._scan_task.done():
            if self._scan_active and self.scan_status != "Cancelling":
                self.scan_status = "Cancelling"
                self._scan_task.cancel()
                self._notify_scan()
            return
        if self._scan_unloading:
            return
        self._scan_active = True
        self.update_interval = None
        self.scan_report = None
        self.scan_timestamp = None
        self.scan_requests = 0
        self.scan_status = f"0/{REGISTER_COUNT} registers analyzed"
        self._scan_last_phase = None
        self._scan_last_progress = 0
        self._notify_scan()
        _LOGGER.info(
            "%s: Starting read-only Modbus datapoint scan (model=%s, "
            "firmware=%s, %d registers, %d coils); normal polling paused",
            self.config_entry.title,
            self.device.model,
            self.device.info.firmware_version or self.device.firmware_reference,
            REGISTER_COUNT,
            COIL_COUNT,
        )
        try:
            self._scan_task = self.config_entry.async_create_background_task(
                self.hass,
                self._async_run_scan(),
                name=f"TROVIS datapoint scan: {self.config_entry.title}",
                eager_start=True,
            )
        except Exception:
            _LOGGER.exception(
                "%s: Could not start Modbus datapoint scan",
                self.config_entry.title,
            )
            self._scan_active = False
            self.update_interval = SCAN_INTERVAL
            self.scan_status = "Failed"
            self.async_set_updated_data(self.device)
            self._notify_scan()
            raise

    def _scan_progress(self, update: ScanProgress) -> None:
        """Throttle only the scan entity; avoid updating all polled entities."""
        self.scan_requests = update.requests
        if (
            update.space != self._scan_last_phase
            or update.analyzed == update.total
            or update.analyzed - self._scan_last_progress >= 200
        ):
            self.scan_status = (
                f"{update.analyzed}/{update.total} {update.space} analyzed"
            )
            self._scan_last_phase = update.space
            self._scan_last_progress = update.analyzed
            self._notify_scan()

    async def _async_run_scan(self) -> None:
        """Own the Modbus unit until the scan finishes; always resume polling."""
        try:
            # A poll or HA write already in progress is allowed to finish first.
            async with self._modbus_lock:
                info = self.device.info
                result = await async_scan_datapoints(
                    self.device._unit,
                    model=self.device.model,
                    firmware=(
                        info.firmware_version or str(self.device.firmware_reference)
                    ),
                    hardware=info.hardware_version,
                    system_code=(
                        str(info.system_code) if info.system_code is not None else None
                    ),
                    # The HA-local unit proxy already retries timeouts twice.
                    retries=0,
                    progress=self._scan_progress,
                )
            self.scan_status = result.status
            self.scan_report = result.report
            self.scan_timestamp = datetime.now(UTC).isoformat(timespec="seconds")
            self.scan_requests = result.requests
            _LOGGER.info(
                "%s: Modbus datapoint scan %s after %.1f s / %d read operations; "
                "normal polling resuming",
                self.config_entry.title,
                result.status,
                result.elapsed_seconds,
                result.requests,
            )
            # Keep the complete report visible with HA's default WARNING level.
            _LOGGER.warning(
                "%s: Modbus datapoint scan report (%s):\n%s",
                self.config_entry.title,
                result.status,
                result.report,
            )
        except asyncio.CancelledError:
            self.scan_status = "Cancelled"
            _LOGGER.info(
                "%s: Modbus datapoint scan cancelled; normal polling resuming",
                self.config_entry.title,
            )
            # Cancellation is an expected user action; do not retain a partial
            # report as if all addresses had been classified.
        except Exception:
            self.scan_status = "Failed"
            _LOGGER.exception(
                "%s: Modbus datapoint scan failed", self.config_entry.title
            )
        finally:
            self._scan_active = False
            self.update_interval = SCAN_INTERVAL
            self._notify_scan()
            try:
                if not self._scan_unloading:
                    # Re-arm scheduled polling even if the immediate refresh fails.
                    self.async_set_updated_data(self.device)
                    await self.async_refresh()
            finally:
                self._scan_task = None

    async def async_stop_scan_for_unload(self) -> None:
        """Cancel and await scan cleanup before unloading the config entry."""
        self._scan_unloading = True
        task = self._scan_task
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _async_update_data(self) -> Trovis557x:
        """Refresh all TROVIS data."""
        started = monotonic()

        if self._scan_active:
            # A scheduled/manual refresh can still arrive during the pause.
            # Keep the last known values without touching the Modbus unit.
            return self.device
        try:
            async with self._modbus_lock:
                if self._scan_active:
                    return self.device
                await self.device.async_update()
        except ModbusError as err:
            # Auto-exclusion confirmation also performs Modbus reads. It must
            # finish before a scan takes ownership of the consumer-local unit.
            if not self._scan_active:
                async with self._modbus_lock:
                    if not self._scan_active:
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
            CONF_EXCLUDED_REGISTERS
            if block.space == "holding"
            else CONF_EXCLUDED_COILS
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
