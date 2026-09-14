"""Repository-level contract tests for F12 control-parameter entities."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "trovis557x"


def _load_json(path: Path) -> dict:
    """Load one JSON file."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def test_control_parameter_entity_id_contract() -> None:
    """Keep every F12 entity under the requested rkX_control_parameter prefix."""
    number_source = (COMPONENT / "number.py").read_text(encoding="utf-8")
    switch_source = (COMPONENT / "switch.py").read_text(encoding="utf-8")

    assert 'prefix = f"rk{index}_control_parameter"' in number_source
    for suffix in (
        "kp",
        "tn",
        "tv",
        "ty",
        "hysteresis",
        "min_on_time",
        "min_off_time",
    ):
        assert f'"{suffix}"' in number_source

    assert 'key=f"{prefix}_control_parameter_mode"' in switch_source
    assert 'key="rk4_control_parameter_mode"' in switch_source


def test_control_parameter_translation_contract() -> None:
    """Keep grouped German names and synchronized English source strings."""
    strings = _load_json(COMPONENT / "strings.json")
    english = _load_json(COMPONENT / "translations" / "en.json")
    german = _load_json(COMPONENT / "translations" / "de.json")

    assert strings == english

    assert german["entity"]["switch"]["control_parameter_mode"]["name"] == (
        "{component} Regelungsart 3-Punkt"
    )

    expected_german_numbers = {
        "control_parameter_kp": "{component} PI/PID Verstärkung (Kp)",
        "control_parameter_tn": "{component} PI/PID Nachstellzeit (Tn)",
        "control_parameter_tv": "{component} PI/PID Vorhaltezeit (Tv)",
        "control_parameter_ty": "{component} PI/PID Ventillaufzeit (Ty)",
        "control_parameter_hysteresis": "{component} Zweipunkt Schaltdifferenz",
        "control_parameter_minimum_on_time": (
            "{component} Zweipunkt Mindest-Einschaltzeit"
        ),
        "control_parameter_minimum_off_time": (
            "{component} Zweipunkt Mindest-Ausschaltzeit"
        ),
    }

    for key, name in expected_german_numbers.items():
        assert german["entity"]["number"][key]["name"] == name


def test_control_parameter_capability_gating_contract() -> None:
    """Keep F12 and two-point values behind library capabilities."""
    number_source = (COMPONENT / "number.py").read_text(encoding="utf-8")
    switch_source = (COMPONENT / "switch.py").read_text(encoding="utf-8")

    assert "coordinator.device.control_parameters_available(index)" in number_source
    assert (
        "coordinator.device.two_point_control_parameters_available(index)"
        in number_source
    )
    assert (
        "coordinator.device.two_point_control_parameters_available(index)"
        in switch_source
    )
