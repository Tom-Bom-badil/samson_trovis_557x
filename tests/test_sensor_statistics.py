"""Repository-level contract tests for physical-sensor statistics attributes."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "trovis557x"
SENSOR = COMPONENT / "sensor.py"
STATISTICS = COMPONENT / "sensor_statistics.py"


def _source(path: Path) -> str:
    """Return one source file as text."""
    return path.read_text(encoding="utf-8")


def test_statistics_helper_is_valid_python() -> None:
    """Keep the isolated recorder helper syntactically valid."""
    ast.parse(_source(STATISTICS))


def test_physical_sensor_statistics_contract() -> None:
    """Keep rolling statistics limited to physical measurement entities."""
    sensor_source = _source(SENSOR)

    assert "PhysicalSensorStatisticsManager" in sensor_source
    assert "STATISTIC_ATTRIBUTE_NAMES" in sensor_source
    assert "_unrecorded_attributes = STATISTIC_ATTRIBUTE_NAMES" in sensor_source

    selector = sensor_source.split("def _uses_physical_sensor_statistics", 1)[1].split(
        "\n\n\n", 1
    )[0]
    assert 'description.component == "sensors"' in selector
    assert 'description.value_kind == "number"' in selector
    assert "SensorStateClass.MEASUREMENT" in selector
    assert 'description.field != "summer_outdoor_temperature_average"' in selector


def test_statistics_are_recorder_backed_and_throttled() -> None:
    """Keep statistics historical, recorder-backed, and five-minute cached."""
    source = _source(STATISTICS)

    assert 'ATTR_MIN_24H: Final = "min_24h"' in source
    assert 'ATTR_MAX_24H: Final = "max_24h"' in source
    assert 'ATTR_MIN_7D: Final = "min_7d"' in source
    assert 'ATTR_MAX_7D: Final = "max_7d"' in source
    assert "timedelta(minutes=5)" in source
    assert "timedelta(hours=24)" in source
    assert "timedelta(days=7)" in source
    assert "statistic_during_period" in source
    assert "async_add_executor_job" in source
    assert "async_write_ha_state" in source

    # Historical statistics are a Home Assistant presentation concern only.
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert not any(module.startswith("trovis_modbus") for module in imported_modules)
