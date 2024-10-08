"""Sensor platform for multi person weight sensor."""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any, Literal, Self

from homeassistant.components import persistent_notification
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorEntityDescription,
    SensorExtraStoredData,
)
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from pydantic import BaseModel, ValidationError

from custom_components.multi_person_weight_sensor.data import (
    MPWSPersonData,
    MPWSStoredData,
    SensorHistoryEntry,
)

from .const import LOGGER
from .entity import MPWSEntity

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import MPWSConfigEntry


class EntityProducingCallback:
    """Callback with access to async_add_entities."""

    async_add_entity: Callable[[PersonWeightSensor], Coroutine[None, None, str | None]]
    sensors: list[PersonWeightSensor]
    threshold: Decimal
    hass: HomeAssistant
    entry: MPWSConfigEntry

    def __init__(
        self,
        async_add_entity: Callable[
            [PersonWeightSensor], Coroutine[None, None, str | None]
        ],
        sensors: list[PersonWeightSensor],
        threshold: Decimal,
        hass: HomeAssistant,
        entry: MPWSConfigEntry,
    ) -> None:
        """Construct the instance."""
        self.async_add_entity = async_add_entity
        self.sensors = sensors
        self.threshold = threshold
        self.hass = hass
        self.entry = entry

    @callback
    def __call__(self, event: Event[EventStateChangedData]) -> None:
        """Handle the source sensor state update."""
        LOGGER.debug(
            f"Source sensor state updated from {event.data['old_state']} to {event.data['new_state']}"  # noqa: E501
        )

        if not event.data["new_state"]:
            LOGGER.warning("State update reported, but there is no new state")
            return

        LOGGER.debug(f"state: {event.data['new_state'].state}")

        try:
            new_value = Decimal(event.data["new_state"].state)
        except InvalidOperation:
            LOGGER.warning(
                f"Non-decimal state for {event.data['entity_id']}: {event.data["new_state"].state}"  # noqa: E501
            )
            return

        for sensor in self.sensors:
            if not sensor.native_value:
                LOGGER.warning(
                    f"Encountered a sensor without a value ({sensor.entity_id}) - cannot compare thresholds"  # noqa: E501
                )
                continue

            if abs(sensor.native_value - new_value) < self.threshold:
                LOGGER.debug(
                    f"Found sensor with value within the treshold: {sensor.entity_id}"
                )
                sensor.add_entry(new_value)
                return

        LOGGER.info(
            f"No mathing sensor found for entry {new_value}. Creating a new one"
        )
        new_person = PersonWeightSensor.from_first_entry(
            name=f"Person {len(self.sensors) + 1}",
            first_entry=new_value,
            config_entry=self.entry,
        )

        future = asyncio.run_coroutine_threadsafe(
            self.async_add_entity(new_person), self.hass.loop
        )

        if not event.data["old_state"] or event.data["old_state"].state == "unknown":
            return

        device_id = future.result()

        persistent_notification.create(
            self.hass,
            title="A new person has weighted themselves",
            message=f'Configure the "{new_person.name}" sensor created [here](/config/devices/device/{device_id})',  # noqa: E501
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MPWSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    raw_data = await entry.runtime_data.storage.async_load()
    data = MPWSStoredData(persons=[]) if not raw_data else MPWSStoredData(**raw_data)

    if len(data.persons) > 0:
        sensors = [
            PersonWeightSensor(name=person.name, config_entry=entry)
            for person in data.persons
        ]
    else:
        state = hass.states.get(entry.runtime_data.options.source)

        if state and state.state != "unknown":
            sensors = [
                PersonWeightSensor.from_first_entry(
                    name="Person 1",
                    config_entry=entry,
                    first_entry=Decimal(state.state),
                )
            ]
        else:
            sensors = []

    async_add_entities(sensors)

    async def add_entity(e: PersonWeightSensor) -> str | None:
        async_add_entities([e])
        sensors.append(e)
        data.persons.append(MPWSPersonData(name=e.name))
        await entry.runtime_data.storage.async_save(data.dict())
        entity_registry = er.async_get(hass)
        entity = entity_registry.async_get(e.entity_id)

        return entity.device_id if entity else None

    entry.runtime_data.unsub_to_state_updates = async_track_state_change_event(
        hass,
        entry.runtime_data.options.source,
        EntityProducingCallback(
            add_entity,
            sensors,
            Decimal.from_float(entry.runtime_data.options.weight_difference_threshold),
            hass=hass,
            entry=entry,
        ),
    )


async def async_unload_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: MPWSConfigEntry,
) -> bool:
    """Unload the sensor entry."""
    if entry.runtime_data.unsub_to_state_updates:
        entry.runtime_data.unsub_to_state_updates()

    return True


class PersonWeightSensorExtraStoredData(SensorExtraStoredData):
    """Extra data for the person weight sensor that needs to be restored."""

    class _Data(BaseModel):
        history: list[SensorHistoryEntry]
        name: str

    _data: _Data

    def __init__(
        self,
        name: str,
        history: list[SensorHistoryEntry],
        native_value: Decimal | None,
        native_unit_of_measurement: str | None = None,
    ) -> None:
        """Initialize the instance."""
        super().__init__(
            native_value=native_value,
            native_unit_of_measurement=native_unit_of_measurement,
        )
        self._data = self._Data(history=history, name=name)

    def as_dict(self) -> dict[str, Any]:
        """Serialize the extra data into a dict."""
        data = super().as_dict()

        data.update(self._data.dict())

        LOGGER.debug(data, stack_info=True)

        return data

    @classmethod
    def from_dict(cls, restored: dict[str, Any]) -> Self | None:
        """Construct the class instance from a restored dict."""
        try:
            return cls(**restored)
        except ValidationError as e:
            LOGGER.warning(
                f"Extra data for person weight sensor could not be restored: {e}"
            )
            LOGGER.debug(restored, stack_info=True)
            return None

    @property
    def history(self):  # noqa: ANN201, D102
        return self._data.history

    @property
    def name(self):  # noqa: ANN201, D102
        return self._data.name


class PersonWeightSensor(MPWSEntity, RestoreSensor):
    """Person weight sensor class."""

    history: list[SensorHistoryEntry]
    name: str

    _attr_native_unit_of_measurement = "kg"
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:weight-kilogram"

    class StateAttributes(BaseModel):
        """Model representing sensor attributes."""

        history: list[SensorHistoryEntry]
        name: str
        is_multi_person_weight_sensor: Literal[True] = True

    def __init__(self, *, name: str, config_entry: MPWSConfigEntry) -> None:
        """Initialize the sensor class."""
        name_id_part = name.lower().replace(" ", "_")
        sensor_id = f"mpws_{config_entry.runtime_data.options.id_safe_name}_{name_id_part}_weight"  # noqa: E501

        super().__init__(unique_id=sensor_id, config_entry=config_entry)

        self.entity_id = f"sensor.{sensor_id}"
        self.entity_description = SensorEntityDescription(
            key=name,
            device_class=SensorDeviceClass.WEIGHT,
            state_class=SensorStateClass.MEASUREMENT,
        )
        self.history = []
        self.name = name

    @classmethod
    def from_first_entry(
        cls, *, name: str, config_entry: MPWSConfigEntry, first_entry: Decimal
    ) -> Self:
        """Create person weight sensor instance with a new entry."""
        instance = cls(name=name, config_entry=config_entry)

        instance.history.append(
            SensorHistoryEntry(
                value=float(first_entry),
                timestamp=str(datetime.now()),  # noqa: DTZ005
            )
        )

        return instance

    def add_entry(self, entry: Decimal) -> None:
        """Add new entry to the sensor history and update it's state."""
        self.history.append(
            SensorHistoryEntry(
                value=float(entry),
                timestamp=str(datetime.now()),  # noqa: DTZ005
            )
        )
        asyncio.run_coroutine_threadsafe(self._update_ha_state(), self.hass.loop)

    async def _update_ha_state(self) -> None:
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity being added to HA."""
        await super().async_added_to_hass()

        if (last_sensor_data := await self.async_get_last_sensor_data()) is not None:
            self.name = last_sensor_data.name
            self.history = last_sensor_data.history

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the sensor."""
        return self.StateAttributes(
            history=self.history,
            name=self.name,
        ).dict()

    @property
    def native_value(self) -> Decimal | None:
        """Return the native value of the sensor."""
        if len(self.history) > 0:
            return Decimal.from_float(self.history[-1].value)

        return None

    @property
    def extra_restore_state_data(self) -> PersonWeightSensorExtraStoredData:
        """Return additional sensor state to be restored."""
        return PersonWeightSensorExtraStoredData(
            native_value=self.native_value,
            native_unit_of_measurement=self.native_unit_of_measurement,
            history=self.history,
            name=self.name,
        )

    async def async_get_last_sensor_data(
        self,
    ) -> PersonWeightSensorExtraStoredData | None:
        """Restore extra sensor data."""
        if (restored_last_extra_data := await self.async_get_last_extra_data()) is None:
            return None

        return PersonWeightSensorExtraStoredData.from_dict(
            restored_last_extra_data.as_dict()
        )
