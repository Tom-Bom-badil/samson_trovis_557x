"""HA-specific presentation specs for TROVIS datapoints."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.helpers.entity import EntityCategory


@dataclass(frozen=True, kw_only=True)
class TrovisFieldSpec:
    """HA-specific selection and presentation override for a TROVIS datapoint."""

    key: str
    component: str
    field: str
    translation_key: str | None = None
    translation_placeholders: dict[str, str] | None = None

    entity_category: EntityCategory | None = None
    entity_registry_enabled_default: bool = True

    # HA-specific overrides.
    device_class: str | None = None
    native_unit_of_measurement: str | None = None
    mode: object | None = None
