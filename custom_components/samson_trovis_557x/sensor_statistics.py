"""Recorder-backed rolling statistics for physical TROVIS sensor entities."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from typing import Final

from homeassistant.components.recorder.statistics import statistic_during_period
from homeassistant.components.recorder.util import get_instance
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

ATTR_MIN_24H: Final = "min_24h"
ATTR_MAX_24H: Final = "max_24h"
ATTR_MIN_7D: Final = "min_7d"
ATTR_MAX_7D: Final = "max_7d"

STATISTIC_ATTRIBUTE_NAMES: Final = frozenset(
    {ATTR_MIN_24H, ATTR_MAX_24H, ATTR_MIN_7D, ATTR_MAX_7D}
)

_REFRESH_INTERVAL: Final = timedelta(minutes=5)
_INITIAL_REFRESH_DELAY: Final = timedelta(seconds=10)
_TYPES: Final = {"min", "max"}

StatisticsAttributes = dict[str, float | None]


def _empty_attributes() -> StatisticsAttributes:
    """Return the stable attribute shape used before recorder data exists."""
    return {
        ATTR_MIN_24H: None,
        ATTR_MAX_24H: None,
        ATTR_MIN_7D: None,
        ATTR_MAX_7D: None,
    }


def _number_or_none(value: object) -> float | None:
    """Return a recorder statistic as float when it is numeric."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _period_min_max(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
) -> tuple[float | None, float | None]:
    """Return the recorder min/max aggregate for one exact rolling period."""
    summary = statistic_during_period(
        hass,
        start,
        end,
        entity_id,
        _TYPES,
        units={},
    )
    if not isinstance(summary, Mapping):
        return None, None

    return _number_or_none(summary.get("min")), _number_or_none(summary.get("max"))


def _load_statistics(
    hass: HomeAssistant,
    entity_ids: tuple[str, ...],
    now: datetime,
) -> dict[str, StatisticsAttributes]:
    """Load the two rolling min/max windows in the recorder DB executor."""
    start_24h = now - timedelta(hours=24)
    start_7d = now - timedelta(days=7)
    result: dict[str, StatisticsAttributes] = {}

    for entity_id in entity_ids:
        min_24h, max_24h = _period_min_max(hass, entity_id, start_24h, now)
        min_7d, max_7d = _period_min_max(hass, entity_id, start_7d, now)
        result[entity_id] = {
            ATTR_MIN_24H: min_24h,
            ATTR_MAX_24H: max_24h,
            ATTR_MIN_7D: min_7d,
            ATTR_MAX_7D: max_7d,
        }

    return result


class PhysicalSensorStatisticsManager:
    """Cache recorder min/max statistics for physical TROVIS measurements."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._entities: dict[str, Entity] = {}
        self._attributes: dict[str, StatisticsAttributes] = {}
        self._refresh_lock = asyncio.Lock()
        self._cancel_initial_refresh: Callable[[], None] | None = None
        self._cancel_interval: Callable[[], None] | None = None

    @callback
    def register(self, entity: Entity) -> None:
        """Register one physical sensor after Home Assistant assigned its ID."""
        entity_id = entity.entity_id
        if entity_id is None:
            return

        self._entities[entity_id] = entity
        self._attributes.setdefault(entity_id, _empty_attributes())

    @callback
    def unregister(self, entity_id: str) -> None:
        """Forget one sensor when its entity is removed."""
        self._entities.pop(entity_id, None)
        self._attributes.pop(entity_id, None)

    @callback
    def start(self) -> None:
        """Start the delayed first refresh and five-minute refresh cycle."""
        if self._cancel_interval is not None:
            return

        self._cancel_initial_refresh = async_call_later(
            self.hass,
            _INITIAL_REFRESH_DELAY,
            self.async_refresh,
        )
        self._cancel_interval = async_track_time_interval(
            self.hass,
            self.async_refresh,
            _REFRESH_INTERVAL,
        )

    @callback
    def stop(self) -> None:
        """Stop scheduled recorder refreshes."""
        if self._cancel_initial_refresh is not None:
            self._cancel_initial_refresh()
            self._cancel_initial_refresh = None
        if self._cancel_interval is not None:
            self._cancel_interval()
            self._cancel_interval = None

        self._entities.clear()
        self._attributes.clear()

    @callback
    def attributes(self, entity_id: str | None) -> StatisticsAttributes:
        """Return cached rolling statistics for an entity."""
        if entity_id is None:
            return _empty_attributes()
        return dict(self._attributes.get(entity_id, _empty_attributes()))

    async def async_refresh(self, now: datetime | None = None) -> None:
        """Refresh cached recorder statistics and publish changed attributes."""
        if not self._entities or self._refresh_lock.locked():
            return

        if "recorder" not in self.hass.config.components:
            return

        async with self._refresh_lock:
            entity_ids = tuple(self._entities)
            query_time = dt_util.as_utc(now) if now is not None else dt_util.utcnow()

            try:
                recorder = get_instance(self.hass)
                refreshed = await recorder.async_add_executor_job(
                    _load_statistics,
                    self.hass,
                    entity_ids,
                    query_time,
                )
            except (KeyError, RuntimeError):
                # Recorder can still be starting up or already shutting down.
                return
            except Exception:
                # Historical attributes are optional comfort data. A recorder
                # problem must never affect the live Modbus sensor state.
                _LOGGER.debug(
                    "Unable to refresh TROVIS physical-sensor statistics",
                    exc_info=True,
                )
                return

            for entity_id, attributes in refreshed.items():
                if self._attributes.get(entity_id) == attributes:
                    continue

                self._attributes[entity_id] = attributes
                if (entity := self._entities.get(entity_id)) is not None:
                    entity.async_write_ha_state()
