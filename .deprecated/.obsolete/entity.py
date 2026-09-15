"""Base entity for Trovis 557x.

Each active Rk slot and the physical measurement inputs are their own
(sub-)devices, linked to the controller via ``via_device``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo, async_generate_entity_id
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify
from trovis_modbus import (
    ControlCircuitRole,
    TrovisValueValidationError,
    TrovisWriteAccessDisabledError,
    TrovisWriteAccessError,
    TrovisWriteNotImplementedError,
)

from .const import CONF_SLUG, DEFAULT_SLUG, DOMAIN
from .coordinator import TrovisCoordinator


def rk1_to_rk3_indices(coordinator: TrovisCoordinator) -> tuple[int, ...]:
    """Return active technical Rk1-Rk3 slots for this hydronic system."""
    return tuple(
        index for index in coordinator.device.control_circuit_indices if index <= 3
    )


def _rk_sub_device(
    coordinator: TrovisCoordinator,
    index: int,
) -> tuple[str, str, str]:
    """Return identity and role-aware presentation for one Rk sub-device."""
    role = coordinator.device.control_circuit_role(index)
    component = f"rk{index}"

    if role is ControlCircuitRole.HEATING:
        return (
            component,
            f"Rk{index} – Heating circuit {index}",
            f"{component}_heating",
        )
    if role is ControlCircuitRole.PRECONTROL:
        return component, f"Rk{index} – Precontrol circuit", f"{component}_precontrol"
    if role is ControlCircuitRole.BUFFER_TANK:
        return (
            component,
            f"Rk{index} – Buffer tank circuit",
            f"{component}_buffer_tank",
        )
    if role is ControlCircuitRole.DOMESTIC_HOT_WATER:
        return component, "Rk4 – Domestic hot water", "rk4_dhw"

    return component, f"Rk{index} – Control circuit {index}", component


def _sub_device(
    coordinator: TrovisCoordinator,
    component: str,
) -> tuple[str, str, str] | None:
    """Return (sub-device id, fallback name, translation key), or None."""
    if component == "sensors":
        return "measurements", "Measurements", "measurements"

    if component == "solar":
        return "solar", "Solar – Solar circuit", "solar"

    if component == "buffer_tank":
        return _rk_sub_device(coordinator, 1)

    if component.startswith("rk") and component[2:].isdigit():
        index = int(component[2:])
        if 1 <= index <= 4:
            return _rk_sub_device(coordinator, index)

    return None


def _entry_slug(value: object) -> str:
    """Return a Home Assistant friendly entity prefix."""
    return slugify(str(value or "")) or DEFAULT_SLUG


class TrovisEntity(CoordinatorEntity[TrovisCoordinator]):
    """Common identity + device-info for every Trovis entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        key: str,
        component: str,
        platform: str,
        translation_key: str | None = None,
        translation_placeholders: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._component = component

        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = translation_key or key
        self._attr_translation_placeholders = dict(translation_placeholders or {})

        entity_slug = _entry_slug(entry.data.get(CONF_SLUG, entry.title))
        object_id = f"{entity_slug}_{key}"

        self._attr_suggested_object_id = object_id
        self.entity_id = async_generate_entity_id(
            f"{platform}.{{}}",
            object_id,
            hass=coordinator.hass,
        )

        info = coordinator.device.info
        sub = _sub_device(coordinator, component)
        if sub is None:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entry.entry_id)},
                manufacturer=info.manufacturer,
                model=info.model,
                name=entry.title,
                sw_version=info.firmware_version,
                hw_version=info.hardware_version,
                serial_number=info.serial_number,
            )
        else:
            sub_id, sub_name, sub_translation_key = sub
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{entry.entry_id}_{sub_id}")},
                manufacturer=info.manufacturer,
                name=sub_name,
                translation_key=sub_translation_key,
                via_device=(DOMAIN, entry.entry_id),
            )

    @property
    def _subsystem(self) -> Any:
        """Return the shared library component used by this entity."""
        return getattr(self.coordinator.device, self._component)

    async def _async_write_datapoint(self, field: str, value: object) -> None:
        """Write one library datapoint and refresh the shared coordinator."""
        if not self.coordinator.device.writing_enabled:
            raise HomeAssistantError("Please enable writing for changes!")

        try:
            await self._subsystem.async_write_datapoint(
                field,
                value,
                access_code=self.coordinator.access_code,
            )
        except (
            TrovisWriteAccessDisabledError,
            TrovisWriteAccessError,
            TrovisValueValidationError,
        ) as err:
            raise HomeAssistantError(str(err)) from err
        except TrovisWriteNotImplementedError as err:
            raise HomeAssistantError(
                "Writing TROVIS data points is not implemented yet"
            ) from err

        await self.coordinator.async_request_refresh()
