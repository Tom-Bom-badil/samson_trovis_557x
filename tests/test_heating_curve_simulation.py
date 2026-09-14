"""Contract tests for the TROVIS heating-curve simulation UI helper."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "trovis557x"
TRANSLATIONS = COMPONENT / "translations"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_simulation_helper_translation_contract() -> None:
    """Keep strings/en identical and preserve the simulation helper key."""
    strings = _load_json(COMPONENT / "strings.json")
    english = _load_json(TRANSLATIONS / "en.json")
    german = _load_json(TRANSLATIONS / "de.json")

    assert strings == english
    assert (
        strings["entity"]["sensor"]["ui_helper_simulation_values"]["name"]
        == "Helper - {component} simulation values"
    )
    assert (
        german["entity"]["sensor"]["ui_helper_simulation_values"]["name"]
        == "Helper - {component} Simulationswerte"
    )


def test_simulation_helper_entity_contract() -> None:
    """Keep the helper local, hidden, and named from the controller slug."""
    simulation_source = (COMPONENT / "simulation.py").read_text(encoding="utf-8")
    sensor_source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")

    assert 'f"ui_helper_rk{index}_simulation_values"' in simulation_source
    assert 'translation_key="ui_helper_simulation_values"' in simulation_source
    assert "self._attr_device_info = None" in simulation_source
    assert "_attr_entity_registry_visible_default = False" in simulation_source
    assert "self._subsystem.heating_curve_parameters()" in simulation_source
    assert "calculate_heating_curve(" in simulation_source
    assert "coordinator.device.room_heating_circuit_indices" in sensor_source
    assert "TrovisHeatingCurveSimulationSensor" in sensor_source


def test_simulation_actions_registered_as_platform_entity_services() -> None:
    """Register both dashboard actions through the current HA entity-service API."""
    init_source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")

    assert "service.async_register_platform_entity_service(" in init_source
    assert 'SERVICE_SET_SIMULATION_VALUE = "set_simulation_value"' in init_source
    assert 'SERVICE_RESET_SIMULATION = "reset_simulation"' in init_source
    assert 'entity_domain="sensor"' in init_source
    assert "func=_async_set_simulation_value" in init_source
    assert "func=_async_reset_simulation" in init_source


def test_simulation_actions_are_local_only() -> None:
    """Changing or resetting simulation data must not use the Modbus write path."""
    simulation_source = (COMPONENT / "simulation.py").read_text(encoding="utf-8")

    assert "async def async_set_simulation_value(" in simulation_source
    assert "async def async_reset_simulation(" in simulation_source
    assert "replace(" in simulation_source
    assert "self.async_write_ha_state()" in simulation_source

    action_block = simulation_source[
        simulation_source.index(
            "async def async_set_simulation_value("
        ) : simulation_source.index("def _curve_attributes(")
    ]
    assert "_async_write_datapoint" not in action_block
    assert "async_write_datapoint" not in action_block


def test_simulation_actions_support_all_three_curve_modes() -> None:
    """Keep slope, four-point, and fixed-setpoint simulation independently writable."""
    simulation_source = (COMPONENT / "simulation.py").read_text(encoding="utf-8")

    assert "HeatingCircuitControlMode.HEATING_CURVE" in simulation_source
    assert "HeatingCircuitControlMode.FOUR_POINT" in simulation_source
    assert "HeatingCircuitControlMode.FIXED_SETPOINT" in simulation_source
    assert '"gradient"' in simulation_source
    assert '"four_point_outdoor_temperature_1"' in simulation_source
    assert '"fixed_setpoint_day"' in simulation_source


def test_simulation_service_description_contract() -> None:
    """Expose target-aware actions and localized names/descriptions."""
    services = (COMPONENT / "services.yaml").read_text(encoding="utf-8")
    strings = _load_json(COMPONENT / "strings.json")
    german = _load_json(TRANSLATIONS / "de.json")

    assert "set_simulation_value:" in services
    assert "reset_simulation:" in services
    assert "integration: trovis557x" in services
    assert "domain: sensor" in services
    assert "- gradient" in services
    assert "- four_point_outdoor_temperature_1" in services
    assert "- fixed_setpoint_day" in services

    assert strings["services"]["set_simulation_value"]["name"] == "Set simulation value"
    assert strings["services"]["reset_simulation"]["name"] == "Reset simulation"
    assert (
        german["services"]["set_simulation_value"]["name"] == "Simulationswert setzen"
    )
    assert german["services"]["reset_simulation"]["name"] == "Simulation zurücksetzen"


def test_simulation_service_validation_translations_exist() -> None:
    """Keep user-facing validation errors translatable in English and German."""
    strings = _load_json(COMPONENT / "strings.json")
    german = _load_json(TRANSLATIONS / "de.json")

    expected = {
        "not_simulation_entity",
        "simulation_field_not_available",
        "simulation_field_not_numeric",
        "simulation_value_out_of_range",
    }
    assert expected <= set(strings["exceptions"])
    assert expected <= set(german["exceptions"])
