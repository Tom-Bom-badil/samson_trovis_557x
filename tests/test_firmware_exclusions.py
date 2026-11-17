"""Standalone compatibility tests for persisted manual/automatic exclusions.

No Home Assistant or Modbus dependency is required for these pure functions.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

COMPONENT = (
    Path(__file__).resolve().parents[1] / "custom_components" / "samson_trovis_557x"
)


def _exclusion_state():
    """Import the real functions with only the necessary package namespace."""
    pkg = "test_standalone_trovis_exclusion"
    for name in (pkg,):
        if name not in sys.modules:
            mod = types.ModuleType(name)
            mod.__path__ = [str(COMPONENT)]
            sys.modules[name] = mod
    # importlib imports the actual read_exclusions and const modules, not mocks.
    return importlib.import_module(f"{pkg}.exclusion_state")


def test_legacy_manual_state_and_no_firmware() -> None:
    m = _exclusion_state()
    old = {"excluded_registers": "4,5-6", "excluded_coils": "19"}
    assert m.option_parts(old["excluded_registers"]) == ("4-6", "")
    assert m.effective_addresses(old, "excluded_registers", 305) == {4, 5, 6}
    upgraded = m.invalidate_stale_automatic(old, 305)
    assert upgraded["excluded_registers"] == {"manual": "4-6", "auto": ""}
    assert upgraded["excluded_coils"] == {"manual": "19", "auto": ""}
    assert upgraded[m.CONF_AUTO_EXCLUSIONS_FIRMWARE] == 305


def test_auto_is_firmware_bound_and_manually_noneditable() -> None:
    m = _exclusion_state()
    old = {
        "excluded_registers": {"manual": "4-6", "auto": "20-22"},
        "excluded_coils": {"manual": "19", "auto": "30"},
        m.CONF_AUTO_EXCLUSIONS_FIRMWARE: 263,
        "heat_meter_indices": [1],
    }
    assert m.effective_addresses(old, "excluded_registers", 263) == {
        4,
        5,
        6,
        20,
        21,
        22,
    }
    assert m.effective_addresses(old, "excluded_registers", 305) == {4, 5, 6}
    manual = m.with_manual(old, "excluded_registers", "8-9")
    assert manual["excluded_registers"] == {"manual": "8-9", "auto": "20-22"}
    assert old["excluded_registers"]["manual"] == "4-6"
    stale = m.invalidate_stale_automatic(old, 305)
    assert stale["excluded_registers"] == {"manual": "4-6", "auto": ""}
    assert stale["excluded_coils"] == {"manual": "19", "auto": ""}
    assert stale["heat_meter_indices"] == [1]
    assert stale[m.CONF_AUTO_EXCLUSIONS_FIRMWARE] == 305


def test_both_spaces_preserve_separation_and_limit() -> None:
    m = _exclusion_state()
    options = {"excluded_registers": "4,5", "excluded_coils": "9"}
    found = m.with_confirmed_automatic(options, 305, {10, 11}, {30})
    assert found["excluded_registers"] == {"manual": "4-5", "auto": "10-11"}
    assert found["excluded_coils"] == {"manual": "9", "auto": "30"}
    after = m.with_confirmed_automatic(found, 305, {11, 12}, set())
    assert after["excluded_registers"]["auto"] == "10-12"
    cleared = m.clear_automatic(after)
    assert cleared["excluded_registers"] == {"manual": "4-5", "auto": ""}
    assert cleared["excluded_coils"] == {"manual": "9", "auto": ""}
    assert m.CONF_AUTO_EXCLUSIONS_FIRMWARE not in cleared
    changed = m.invalidate_for_model_change(after)
    assert changed["excluded_registers"]["manual"] == "4-5"
    assert changed["excluded_coils"]["manual"] == "9"
    assert m.CONF_AUTO_EXCLUSIONS_FIRMWARE not in changed
    with pytest.raises(ValueError, match="safety limit"):
        m.with_confirmed_automatic(after, 305, set(range(65)), set())


def test_bad_data_not_silently_accepted() -> None:
    m = _exclusion_state()
    for value in ({"manual": [1], "auto": ""}, {"manual": "2", "auto": [-1]}, 123):
        with pytest.raises(ValueError):
            m.option_parts(value)
