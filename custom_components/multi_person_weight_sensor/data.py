"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from homeassistant.config_entries import ConfigEntry
from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.storage import Store


class SensorHistoryEntry(BaseModel):
    """Represents an entry in the measurement history array."""

    value: float
    timestamp: str


class MPWSPersonData(BaseModel):
    """Model representing a person's data."""

    name: str


class MPWSStoredData(BaseModel):
    """Model that represents data saved in the config entry by the integration."""

    persons: list[MPWSPersonData] = []


class MPWSConfigEntryOptions(BaseModel):
    """Model that represents options saved in the config entry by the integration."""

    name: str
    source: str
    weight_difference_threshold: float

    @property
    def id_safe_name(self) -> str:
        """Entry name that can be used in an identifier."""
        return self.name.lower().replace(" ", "_")


@dataclass
class MPWSRuntimeData:
    """Runtime data for the Multi Person Weight Sensor integration."""

    options: MPWSConfigEntryOptions
    storage: Store
    unsub_to_state_updates: Callable[[], None] | None = None


class MPWSConfigEntry(ConfigEntry[MPWSRuntimeData]):
    """The integration's config entry."""

    @override
    async def async_remove(self, hass: HomeAssistant) -> None:
        await super().async_remove(hass)
