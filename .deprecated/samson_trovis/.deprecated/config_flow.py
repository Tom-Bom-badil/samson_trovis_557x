"""Config flow for the SAMSON TROVIS integration."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import slugify
from .api import TrovisApi
from .transport import TrovisTransport

from .constants.areas import DEFAULT_ENABLED_AREAS, SELECTABLE_AREAS
from .constants.config import (
    CONF_ENABLED_AREAS,
    CONF_MODEL,
    CONF_PORT_URL,
    CONF_SLAVE_ID,
    CONF_SLUG,
    DEFAULT_NAME,
    DEFAULT_SLAVE_ID,
    DOMAIN,
)



def _default_slug(name: str) -> str:
    """Return a Home Assistant friendly slug."""
    slug = slugify(name)
    return re.sub(r"_+", "_", slug).strip("_") or "trovis"


def _user_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    """Return the config flow user schema."""
    user_input = user_input or {}
    default_name = user_input.get(CONF_NAME, DEFAULT_NAME)

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=default_name): selector.TextSelector(),
            vol.Required(CONF_PORT_URL, default=user_input.get(CONF_PORT_URL, "")): selector.SerialPortSelector(
                {"extra_recommended_domains": [DOMAIN]}
            ),
            vol.Required(CONF_SLAVE_ID, default=user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=247, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_SLUG, default=user_input.get(CONF_SLUG, _default_slug(default_name))): selector.TextSelector(),
        }
    )


def _options_schema(options: dict[str, Any] | None = None) -> vol.Schema:
    """Return the options flow schema."""
    options = options or {}
    enabled_areas = set(options.get(CONF_ENABLED_AREAS, DEFAULT_ENABLED_AREAS))

    return vol.Schema(
        {
            vol.Required(area, default=area in enabled_areas): selector.BooleanSelector()
            for area in SELECTABLE_AREAS
        }
    )


class TrovisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SAMSON TROVIS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match(
                {
                    CONF_PORT_URL: user_input[CONF_PORT_URL],
                    CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
                }
            )

            model = await self._async_read_model(user_input)

            if model is None:
                errors["base"] = "cannot_connect"
            else:
                entry_data = dict(user_input)
                entry_data[CONF_MODEL] = model

                return self.async_create_entry(
                    title=entry_data[CONF_NAME],
                    data=entry_data,
                    options={CONF_ENABLED_AREAS: list(DEFAULT_ENABLED_AREAS)},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )


    async def _async_read_model(self, user_input: dict[str, Any]) -> str | None:
        """Read the TROVIS model from the controller."""
        transport = TrovisTransport(self.hass, user_input)
        api = TrovisApi(transport)

        try:
            return await api.async_read_model()
        finally:
            await transport.async_close()


    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TrovisOptionsFlowHandler:
        """Create the options flow."""
        return TrovisOptionsFlowHandler(config_entry)


class TrovisOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle SAMSON TROVIS options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            enabled_areas = [area for area, enabled in user_input.items() if enabled]
            return self.async_create_entry(
                title="",
                data={CONF_ENABLED_AREAS: enabled_areas},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(dict(self._config_entry.options)),
        )
