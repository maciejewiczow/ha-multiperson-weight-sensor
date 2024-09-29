"""Adds config flow for Blueprint."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import callback
from homeassistant.helpers import selector as sel
from varname.core import nameof

from .const import DOMAIN
from .data import MPWSConfigEntry, MPWSConfigEntryOptions


class ConfigurationFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Multi Person Weight Sensor."""

    VERSION = 1
    MINOR_VERSION = 0

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle flow initiated by manual reconfiguration."""
        return await self.async_step_user(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("name", "Multi Person Weight Sensor"),
                data={},
                options=MPWSConfigEntryOptions(**user_input).dict(),
            )

        dummy_opts = MPWSConfigEntryOptions(
            name="", source="", weight_difference_threshold=0
        )

        return self.async_show_form(
            data_schema=vol.Schema(
                {
                    vol.Required(
                        nameof(dummy_opts.name),
                        default=(user_input or {}).get(
                            nameof(dummy_opts.name), vol.UNDEFINED
                        ),
                    ): sel.TextSelector(
                        sel.TextSelectorConfig(
                            multiline=False,
                            type=sel.TextSelectorType.TEXT,
                        )
                    ),
                    vol.Required(
                        nameof(dummy_opts.source),
                        default=(user_input or {}).get(
                            nameof(dummy_opts.source), vol.UNDEFINED
                        ),
                    ): sel.EntitySelector(
                        sel.EntitySelectorConfig(
                            device_class="weight",
                        ),
                    ),
                    vol.Required(
                        nameof(dummy_opts.weight_difference_threshold),
                        default=(user_input or {}).get(
                            nameof(dummy_opts.weight_difference_threshold), 10
                        ),
                    ): sel.NumberSelector(
                        sel.NumberSelectorConfig(
                            min=0.5,
                            step=0.5,
                            max=40,
                            unit_of_measurement="kg",
                            mode=sel.NumberSelectorMode.SLIDER,
                        )
                    ),
                },
            ),
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Integration options flow."""

    def __init__(self, config_entry: MPWSConfigEntry) -> None:
        """Initialize options flow instance."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Create the options flow."""
        # TODO: options flow
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "show_things",
                    ): bool
                }
            ),
        )
