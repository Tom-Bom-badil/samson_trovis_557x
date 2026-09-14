"""Repository-level tests for Modbus read-exclusion support."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "trovis557x"
TRANSLATIONS = COMPONENT / "translations"


def _load_read_exclusions_module():
    """Load the standalone parser without importing the integration package."""
    path = COMPONENT / "read_exclusions.py"
    spec = importlib.util.spec_from_file_location("trovis557x_read_exclusions", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict:
    """Load one JSON file."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def test_address_list_parser_and_normalization() -> None:
    """Accept support-friendly address/range syntax and normalize it."""
    module = _load_read_exclusions_module()

    assert module.parse_address_list("") == frozenset()
    assert module.parse_address_list("22, 33-35, 119") == frozenset(
        {22, 33, 34, 35, 119}
    )
    assert module.normalize_address_list("35, 33-34, 22, 119, 34") == ("22,33-35,119")


@pytest.mark.parametrize(
    "value",
    (
        "22,,41",
        "foo",
        "33-12",
        "-1",
        "65536",
        "1-2-3",
    ),
)
def test_invalid_address_lists_are_rejected(value: str) -> None:
    """Reject malformed, descending or non-Modbus addresses."""
    module = _load_read_exclusions_module()

    with pytest.raises(ValueError):
        module.parse_address_list(value)


def test_read_exclusion_platform_contract() -> None:
    """Keep both controller-local read-exclusion text entities wired to runtime."""
    init_source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")
    text_source = (COMPONENT / "text.py").read_text(encoding="utf-8")
    strings = _load_json(COMPONENT / "strings.json")
    english = _load_json(TRANSLATIONS / "en.json")
    german = _load_json(TRANSLATIONS / "de.json")

    assert "Platform.TEXT" in init_source
    assert "excluded_registers=excluded_registers" in init_source
    assert "excluded_coils=excluded_coils" in init_source

    assert 'key="excluded_registers"' in text_source
    assert 'key="excluded_coils"' in text_source
    assert '"controller"' in text_source
    assert "EntityCategory.CONFIG" in text_source
    assert "async_schedule_reload(entry.entry_id)" in text_source

    assert strings == english

    for translations in (strings, german):
        assert "excluded_registers" in translations["entity"]["text"]
        assert "excluded_coils" in translations["entity"]["text"]
        assert translations["entity"]["text"]["excluded_registers"]["name"]
        assert translations["entity"]["text"]["excluded_coils"]["name"]
