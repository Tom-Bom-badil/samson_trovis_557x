"""Select entities for enum-backed TROVIS values and dashboard helpers."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from trovis_modbus.metadata import EnumMetadata

from . import (
    TrovisEntity,
    _entry_slug,
    component_supports_datapoint,
    require_enum_metadata,
    rk1_to_rk3_indices,
)
from .const import CONF_SLUG, DOMAIN
from .coordinator import TrovisConfigEntry, TrovisCoordinator

_DASHBOARD_CONTROLLER_SELECT_DATA_KEY = "ui_helper_selected_controller_entity"
_DASHBOARD_CONTROLLER_SELECT_KEY = "ui_helper_selected_controller"


@dataclass(frozen=True, kw_only=True)
class TrovisSelectDescription(SelectEntityDescription):
    """Describe a Trovis select entity.

    Options and enum values come from trovis-modbus. This description only
    selects the field and stores Home Assistant presentation values.
    """

    component: str
    field: str
    translation_placeholders: dict[str, str] | None = None


def _operation_mode(
    component: str,
    key: str,
    placeholder: str,
) -> TrovisSelectDescription:
    """Return an operation-mode select description."""
    return TrovisSelectDescription(
        key=key,
        translation_key="operation_mode",
        name=f"{placeholder} - Operating mode",
        component=component,
        field="mode",
        # This is a control entity, not a config entity:
        # entity_category=EntityCategory.CONFIG,
        translation_placeholders={"component": placeholder},
    )


_SELECTS: tuple[TrovisSelectDescription, ...] = (
    _operation_mode("rk1", "rk1_operating_mode", "Rk1"),
    _operation_mode("rk2", "rk2_operating_mode", "Rk2"),
    _operation_mode("rk3", "rk3_operating_mode", "Rk3"),
    _operation_mode("rk4", "rk4_operation_mode", "Rk4"),
    TrovisSelectDescription(
        key="rk4_disinfection_weekday",
        translation_key="disinfection_weekday",
        name="Rk4 disinfection weekday",
        component="rk4",
        field="disinfection_weekday",
        entity_category=EntityCategory.CONFIG,
        translation_placeholders={"component": "Rk4"},
    ),
)


def _build_dashboard_controllers(hass: HomeAssistant) -> list[dict[str, str]]:
    """Build the controller list used by the global dashboard helper."""
    controllers: list[dict[str, str]] = []

    for entry in hass.config_entries.async_entries(DOMAIN):
        slug = _entry_slug(entry.data.get(CONF_SLUG, entry.title))
        controllers.append(
            {
                "label": entry.title,
                "slug": slug,
                "entry_id": entry.entry_id,
            }
        )

    labels = [controller["label"] for controller in controllers]
    for controller in controllers:
        if labels.count(controller["label"]) > 1:
            controller["label"] = f"{controller['label']} ({controller['slug']})"

    controllers.sort(key=lambda item: item["label"].lower())
    return controllers


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TrovisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Trovis select entities."""
    coordinator = entry.runtime_data

    active_components = {f"rk{index}" for index in rk1_to_rk3_indices(coordinator)}
    if coordinator.device.has_rk4:
        active_components.add("rk4")

    entities: list[SelectEntity] = [
        TrovisSelect(coordinator, description)
        for description in _SELECTS
        if description.component in active_components
        and component_supports_datapoint(
            getattr(coordinator.device, description.component),
            description.field,
        )
    ]

    domain_data = hass.data.setdefault(DOMAIN, {})
    dashboard_select = domain_data.get(_DASHBOARD_CONTROLLER_SELECT_DATA_KEY)
    if dashboard_select is None:
        dashboard_select = TrovisDashboardControllerSelect(hass)
        domain_data[_DASHBOARD_CONTROLLER_SELECT_DATA_KEY] = dashboard_select
        entities.append(dashboard_select)
    else:
        dashboard_select.async_refresh_controllers()

    async_add_entities(entities)


class TrovisDashboardControllerSelect(RestoreEntity, SelectEntity):
    """Global controller selector used by TROVIS dashboards."""

    _attr_has_entity_name = True
    _attr_translation_key = "dashboard_helper_controller_selected"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._attr_unique_id = f"{DOMAIN}_{_DASHBOARD_CONTROLLER_SELECT_KEY}"
        self.entity_id = f"select.{DOMAIN}_{_DASHBOARD_CONTROLLER_SELECT_KEY}"
        self._selected_slug: str | None = None

    async def async_added_to_hass(self) -> None:
        """Restore the previously selected controller."""
        await super().async_added_to_hass()

        if last_state := await self.async_get_last_state():
            restored_slug = last_state.attributes.get("selected_slug")
            if isinstance(restored_slug, str) and restored_slug:
                self._selected_slug = restored_slug

        self._ensure_valid_selection()

    async def async_will_remove_from_hass(self) -> None:
        """Clear the shared reference when this helper is removed."""
        domain_data = self._hass.data.get(DOMAIN)
        if (
            isinstance(domain_data, dict)
            and domain_data.get(_DASHBOARD_CONTROLLER_SELECT_DATA_KEY) is self
        ):
            domain_data.pop(_DASHBOARD_CONTROLLER_SELECT_DATA_KEY, None)

    def async_refresh_controllers(self) -> None:
        """Refresh state after another TROVIS config entry is added."""
        self._ensure_valid_selection()
        if getattr(self, "platform", None) is not None:
            self.async_write_ha_state()

    def _controllers(self) -> list[dict[str, str]]:
        """Return the currently configured TROVIS controllers."""
        return _build_dashboard_controllers(self._hass)

    def _controller_by_slug(self, slug: str | None) -> dict[str, str] | None:
        """Find a configured controller by entity slug."""
        if not slug:
            return None

        for controller in self._controllers():
            if controller["slug"] == slug:
                return controller
        return None

    def _controller_by_label(self, label: str) -> dict[str, str] | None:
        """Find a configured controller by display label."""
        for controller in self._controllers():
            if controller["label"] == label:
                return controller
        return None

    def _ensure_valid_selection(self) -> None:
        """Ensure that the selected controller still exists."""
        if self._controller_by_slug(self._selected_slug):
            return

        controllers = self._controllers()
        self._selected_slug = controllers[0]["slug"] if controllers else None

    @property
    def device_info(self) -> None:
        """Return no device information for this global dashboard helper."""
        return None

    @property
    def options(self) -> list[str]:
        """Return configured controller labels."""
        return [controller["label"] for controller in self._controllers()]

    @property
    def current_option(self) -> str | None:
        """Return the currently selected controller label."""
        selected = self._controller_by_slug(self._selected_slug)
        return selected["label"] if selected else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return metadata used by dashboard templates."""
        selected = self._controller_by_slug(self._selected_slug)
        return {
            "selected_slug": selected["slug"] if selected else "",
            "entity_prefix": selected["slug"] if selected else "",
            "selected_entry_id": selected["entry_id"] if selected else "",
            "available_controllers": self._controllers(),
        }

    async def async_select_option(self, option: str) -> None:
        """Select the controller used by the dashboard."""
        selected = self._controller_by_label(option)
        if selected is None:
            raise HomeAssistantError(f"Unknown TROVIS controller: {option}")

        self._selected_slug = selected["slug"]
        self.async_write_ha_state()


class TrovisSelect(TrovisEntity, SelectEntity):
    """Trovis select entity."""

    entity_description: TrovisSelectDescription

    def __init__(
        self,
        coordinator: TrovisCoordinator,
        description: TrovisSelectDescription,
    ) -> None:
        super().__init__(
            coordinator,
            description.key,
            description.component,
            "select",
            translation_key=description.translation_key,
            translation_placeholders=description.translation_placeholders,
        )
        self.entity_description = description
        enum_metadata = require_enum_metadata(self._subsystem, description.field)
        self._enum_metadata: EnumMetadata = enum_metadata

        self._option_by_key = {option.key: option for option in enum_metadata.options}
        self._key_by_value = {
            int(option.value): option.key for option in enum_metadata.options
        }
        self._attr_options = list(self._option_by_key)
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        value = getattr(self._subsystem, self.entity_description.field)
        if value is None:
            return None
        try:
            return self._key_by_value.get(int(value))
        except (TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        try:
            selected = self._option_by_key[option]
        except KeyError as err:
            raise HomeAssistantError(f"Unsupported TROVIS option: {option}") from err
        await self._async_write_datapoint(
            self.entity_description.field,
            self._enum_metadata.enum_type(selected.value),
        )
