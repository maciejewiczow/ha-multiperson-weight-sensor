"""
Custom integration to split one weight sensor into multiple sensors, each for one person using the scales.

For more details about this integration, please refer to
https://github.com/maciejewiczow/ha-multiperson-weight-sensor
"""  # noqa: E501

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.storage import Store

from .const import DOMAIN, LOGGER
from .data import MPWSConfigEntryOptions, MPWSRuntimeData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import MPWSConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: MPWSConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    LOGGER.debug(entry.options, stack_info=True)

    opts = MPWSConfigEntryOptions(**entry.options)

    entry.runtime_data = MPWSRuntimeData(
        storage=Store(hass, version=1, key=f"{DOMAIN}.{opts.id_safe_name}"),
        options=opts,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: MPWSConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    LOGGER.debug("Entry removed")
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: MPWSConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
