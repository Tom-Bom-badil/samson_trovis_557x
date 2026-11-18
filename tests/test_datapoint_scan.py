"""Static contracts for HA wiring without importing Home Assistant in CI."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "samson_trovis_557x"


def test_scan_buttons_and_root_sensor_are_connected() -> None:
    button = (COMPONENT / "button.py").read_text(encoding="utf-8")
    sensor = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    coordinator = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    init = (COMPONENT / "__init__.py").read_text(encoding="utf-8")
    assert "ZZ - Sniffer Start / Stop (takes time!)" in button
    assert "TrovisDatapointScanButton(entry.runtime_data)" in button
    assert '"controller",\n            "button"' in button
    assert "TrovisModbusAddressScanSensor(coordinator)" in sensor
    assert '"controller",\n            "sensor"' in sensor
    assert "_unrecorded_attributes = frozenset({MATCH_ALL})" in sensor
    assert "register_scan_listener(self.async_write_ha_state)" in sensor
    assert "async_toggle_scan" in coordinator
    assert "async_stop_scan_for_unload" in init
    assert "async_modbus_write_guard" in coordinator
    assert "async_modbus_write_guard" in init
    assert "async_modbus_write_guard" in (COMPONENT / "switch.py").read_text()
    assert "async_modbus_write_guard" in (COMPONENT / "select.py").read_text()
    assert "update_interval = None" in coordinator
    assert "update_interval = SCAN_INTERVAL" in coordinator
    assert "async_scan_datapoints(" in coordinator
    assert "update.analyzed - self._scan_last_progress >= 200" in coordinator
    assert "_scan_last_update" not in coordinator
    assert "Starting read-only Modbus datapoint scan" in coordinator
    assert "Modbus datapoint scan cancelled; normal polling resuming" in coordinator
    assert "Modbus datapoint scan %s after %.1f s" in coordinator
    assert "_LOGGER.warning(" in coordinator
    assert "Modbus datapoint scan report (%s)" in coordinator


def test_translations_are_complete() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text())
    english = json.loads((COMPONENT / "translations" / "en.json").read_text())
    german = json.loads((COMPONENT / "translations" / "de.json").read_text())
    assert strings == english
    for value in (strings, german):
        assert value["entity"]["button"]["datapoint_scan"]["name"]
        assert (
            value["entity"]["sensor"]["datapoint_scan"]["name"]
            == "ZZ - Sniffer Status"
        )
    assert strings["entity"]["button"]["datapoint_scan"]["name"] == (
        "ZZ - Sniffer Start / Stop (takes time!)"
    )
    assert german["entity"]["button"]["datapoint_scan"]["name"] == (
        "ZZ - Sniffer Start / Stop (dauert!)"
    )
