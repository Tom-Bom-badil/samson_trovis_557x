"""Contract tests for controller identity diagnostic sensors."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "trovis557x"
TRANSLATIONS = COMPONENT / "translations"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_controller_identity_diagnostic_sensor_contract() -> None:
    """Expose four existing controller identity values as diagnostics."""
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")

    expected = {
        "controller_model_code": "model_code",
        "controller_firmware": "firmware_version",
        "controller_hardware_version": "hardware_version",
        "controller_serial_number": "serial_number",
    }
    for key, field in expected.items():
        assert f'key="{key}"' in source
        assert f'field="{field}"' in source

    assert source.count('component="info"') >= 4
    assert source.count("entity_category=EntityCategory.DIAGNOSTIC") >= 4


def test_controller_identity_diagnostic_translations() -> None:
    """Keep requested German names and matching English translations."""
    strings = _load_json(COMPONENT / "strings.json")
    english = _load_json(TRANSLATIONS / "en.json")
    german = _load_json(TRANSLATIONS / "de.json")

    assert strings == english
    assert german["entity"]["sensor"]["controller_model_code"]["name"] == (
        "Regler: Modellcode"
    )
    assert german["entity"]["sensor"]["controller_firmware"]["name"] == (
        "Regler: Firmware"
    )
    assert german["entity"]["sensor"]["controller_hardware_version"]["name"] == (
        "Regler: Hardwareversion"
    )
    assert german["entity"]["sensor"]["controller_serial_number"]["name"] == (
        "Regler: Seriennummer"
    )
