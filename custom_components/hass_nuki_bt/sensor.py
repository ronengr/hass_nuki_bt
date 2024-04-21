"""Sensor platform for hass_nuki_bt."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NukiDataUpdateCoordinator
from .entity import NukiEntity

PARALLEL_UPDATES = 0


@dataclass
class NukiSensorEntityDescription(SensorEntityDescription):
    """A class that describes nuki sensor entities."""

    info_function: Callable | None = lambda slf: slf.device.keyturner_state[slf.sensor]


SENSOR_TYPES: dict[str, NukiSensorEntityDescription] = {
    "name": NukiSensorEntityDescription(
        key="name",
        name="Nuki Device Name",
        icon="mdi:lock",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        info_function=lambda slf: slf.device.config.get(slf.sensor),
    ),
    "rssi": NukiSensorEntityDescription(
        key="rssi",
        name="Bluetooth signal strength",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        info_function=lambda slf: slf.device.rssi,
    ),
    "battery": NukiSensorEntityDescription(
        key="battery",
        name="Battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        info_function=lambda slf: slf.device.battery_percentage,
    ),
    "lock_state": NukiSensorEntityDescription(
        key="lock_state",
        name="Lock state",
        icon="mdi:lock",
        device_class=SensorDeviceClass.ENUM,
    ),
    "door_sensor_state": NukiSensorEntityDescription(
        key="door_state",
        name="Door state",
        icon="mdi:door",
        device_class=SensorDeviceClass.ENUM,
    ),
    "last_lock_action": NukiSensorEntityDescription(
        key="last_lock_action",
        name="Last lock action",
        icon="mdi:door",
        device_class=SensorDeviceClass.ENUM,
    ),
    "last_lock_action_trigger": NukiSensorEntityDescription(
        key="last_lock_action_trigger",
        name="Last Action Trigger",
        icon="mdi:door",
        device_class=SensorDeviceClass.ENUM,
    ),
    "last_lock_action_completion_status": NukiSensorEntityDescription(
        key="last_lock_action_completion_status",
        name="Last action completion status",
        icon="mdi:door",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "nuki_state": NukiSensorEntityDescription(
        key="nuki_state",
        name="Nuki state",
        icon="mdi:lock",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "last_action_user": NukiSensorEntityDescription(
        key="last_action_user",
        name="Last action user name",
        icon="mdi:lock",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        info_function=lambda slf: slf.coordinator.last_nuki_log_entry.get("name"),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nuki sensor based on a config entry."""
    coordinator: NukiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [NukiSensor(coordinator, sensor) for sensor in SENSOR_TYPES]
    async_add_entities(entities)


class NukiSensor(NukiEntity, SensorEntity):
    """Representation of a Nuki sensor."""

    def __init__(self, coordinator: NukiDataUpdateCoordinator, sensor: str) -> None:
        """Initialize the Niki sensor."""
        super().__init__(coordinator)
        self.sensor = sensor
        self._attr_unique_id = f"{coordinator.base_unique_id}-{sensor}"
        self.entity_description = SENSOR_TYPES[sensor]
        self._info_function = self.entity_description.info_function
        self._async_update_attrs()

    def _async_update_attrs(self) -> None:
        """Update the entity attributes."""
        self._attr_native_value = self._info_function(self)
