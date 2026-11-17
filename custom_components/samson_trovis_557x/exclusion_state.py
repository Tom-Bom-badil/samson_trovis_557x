"""Persist manual and firmware-bound automatic Modbus read exclusions.

HA owns the per-config-entry state; the TROVIS library only receives the
merged, zero-based address sets.  Legacy string options remain readable.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import CONF_EXCLUDED_COILS, CONF_EXCLUDED_REGISTERS
from .read_exclusions import (
    format_address_list,
    normalize_address_list,
    parse_address_list,
)

CONF_AUTO_EXCLUSIONS_FIRMWARE = "auto_exclusions_firmware"
OPTION_KEYS = (CONF_EXCLUDED_REGISTERS, CONF_EXCLUDED_COILS)
MAX_AUTOMATIC_EXCLUSIONS_PER_SPACE = 64


def option_parts(value: object) -> tuple[str, str]:
    """Extract canonical manual and automatic lists, including legacy strings."""
    if isinstance(value, str):
        return normalize_address_list(value), ""
    if isinstance(value, Mapping):
        manual = value.get("manual", "")
        auto = value.get("auto", "")
        if not isinstance(manual, str) or not isinstance(auto, str):
            raise ValueError("Modbus exclusion option manual/auto must be strings")
        return normalize_address_list(manual), normalize_address_list(auto)
    if value is None:
        return "", ""
    raise ValueError("Unsupported Modbus exclusion option")


def effective_addresses(
    options: Mapping[str, Any], key: str, firmware: int
) -> frozenset[int]:
    """Return manual plus firmware-matched automatic addresses."""
    manual, automatic = option_parts(options.get(key))
    addresses = set(parse_address_list(manual))
    if options.get(CONF_AUTO_EXCLUSIONS_FIRMWARE) == firmware:
        addresses.update(parse_address_list(automatic))
    return frozenset(addresses)


def with_manual(options: Mapping[str, Any], key: str, manual: str) -> dict[str, Any]:
    """Change manual input without touching the stored auto list or its firmware."""
    _, automatic = option_parts(options.get(key))
    updated = dict(options)
    updated[key] = {"manual": normalize_address_list(manual), "auto": automatic}
    return updated


def with_confirmed_automatic(
    options: Mapping[str, Any],
    firmware: int,
    registers: set[int],
    coils: set[int],
) -> dict[str, Any]:
    """Add confirmed exclusions, retaining manual input and the other address space."""
    updated = dict(options)
    firmware_changed = options.get(CONF_AUTO_EXCLUSIONS_FIRMWARE) != firmware
    for key, newly_found in (
        (CONF_EXCLUDED_REGISTERS, registers),
        (CONF_EXCLUDED_COILS, coils),
    ):
        manual, automatic = option_parts(updated.get(key))
        previous = set() if firmware_changed else set(parse_address_list(automatic))
        combined = previous | newly_found
        if len(combined) > MAX_AUTOMATIC_EXCLUSIONS_PER_SPACE:
            raise ValueError("Automatic Modbus exclusion safety limit reached")
        updated[key] = {"manual": manual, "auto": format_address_list(combined)}
    updated[CONF_AUTO_EXCLUSIONS_FIRMWARE] = firmware
    return updated


def invalidate_stale_automatic(
    options: Mapping[str, Any], firmware: int
) -> dict[str, Any]:
    """Discard old-firmware auto lists, preserve all manual lists."""
    if options.get(CONF_AUTO_EXCLUSIONS_FIRMWARE) == firmware:
        return dict(options)
    updated = dict(options)
    for key in OPTION_KEYS:
        manual, _ = option_parts(updated.get(key))
        updated[key] = {"manual": manual, "auto": ""}
    updated[CONF_AUTO_EXCLUSIONS_FIRMWARE] = firmware
    return updated


def invalidate_for_model_change(options: Mapping[str, Any]) -> dict[str, Any]:
    """Keep manual exclusions; drop auto lists tied to a different model."""
    updated = dict(options)
    for key in OPTION_KEYS:
        manual, _ = option_parts(updated.get(key))
        updated[key] = {"manual": manual, "auto": ""}
    updated.pop(CONF_AUTO_EXCLUSIONS_FIRMWARE, None)
    return updated


def clear_automatic(options: Mapping[str, Any]) -> dict[str, Any]:
    """Explicit local reset: preserve manual and unrelated HA options."""
    updated = dict(options)
    for key in OPTION_KEYS:
        manual, _ = option_parts(updated.get(key))
        updated[key] = {"manual": manual, "auto": ""}
    updated.pop(CONF_AUTO_EXCLUSIONS_FIRMWARE, None)
    return updated
