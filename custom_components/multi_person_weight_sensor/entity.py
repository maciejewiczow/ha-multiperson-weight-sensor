"""BlueprintEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

if TYPE_CHECKING:
    from custom_components.multi_person_weight_sensor.data import MPWSConfigEntry


class MPWSEntity(Entity):
    """MPWSEntity class."""

    def __init__(self, unique_id: str, config_entry: MPWSConfigEntry) -> None:
        """Initialize."""
        super().__init__()
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    config_entry.domain,
                    config_entry.entry_id,
                ),
            },
        )
