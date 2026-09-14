"""Contract tests for the TROVIS Rk4 simulation UI helper."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "trovis557x"


def test_rk4_simulation_helper_entity_contract() -> None:
    """Keep the Rk4 helper local, hidden, and aligned with the Rk1-Rk3 helper."""
    simulation_source = (COMPONENT / "simulation_dhw.py").read_text(encoding="utf-8")
    sensor_source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")

    assert "class TrovisDomesticHotWaterSimulationSensor(" in simulation_source
    assert "TrovisHeatingCurveSimulationSensor" in simulation_source
    assert '"ui_helper_rk4_simulation_values"' in simulation_source
    assert 'translation_key="ui_helper_simulation_values"' in simulation_source
    assert 'translation_placeholders={"component": "Rk4"}' in simulation_source
    assert "self._attr_device_info = None" in simulation_source
    assert "coordinator.device.has_rk4" in sensor_source
    assert "TrovisDomesticHotWaterSimulationSensor(coordinator)" in sensor_source


def test_rk4_simulation_uses_legacy_dashboard_parameter_set() -> None:
    """Preserve the six Rk4 values used by the former YAML simulation."""
    simulation_source = (COMPONENT / "simulation_dhw.py").read_text(encoding="utf-8")

    expected_fields = {
        "setpoint_day",
        "setpoint_night",
        "hysteresis",
        "charging_temperature_boost",
        "maximum_charging_temperature",
        "maximum_return_flow_temperature",
    }
    for field in expected_fields:
        assert field in simulation_source

    assert "self._snapshot_parameters()" in simulation_source
    assert "self.async_write_ha_state()" in simulation_source


def test_rk4_simulation_actions_remain_local_only() -> None:
    """Rk4 simulation changes must use the existing local-only action path."""
    simulation_source = (COMPONENT / "simulation_dhw.py").read_text(encoding="utf-8")

    assert "_async_write_datapoint" not in simulation_source
    assert "async_write_datapoint" not in simulation_source


def test_rk4_simulation_fields_are_exposed_by_service_description() -> None:
    """Expose the Rk4 parameters in Home Assistant's action field selector."""
    services = (COMPONENT / "services.yaml").read_text(encoding="utf-8")

    for field in (
        "setpoint_day",
        "setpoint_night",
        "hysteresis",
        "charging_temperature_boost",
        "maximum_charging_temperature",
        "maximum_return_flow_temperature",
    ):
        assert f"- {field}" in services
