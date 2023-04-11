"""Sensor platform for hass_nuki_bt."""
from __future__ import annotations

from homeassistant.components.bluetooth import async_last_service_info
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

SENSOR_TYPES: dict[str, SensorEntityDescription] = {
    "rssi": SensorEntityDescription(
        key="rssi",
        name="Bluetooth signal strength",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "battery": SensorEntityDescription(
        key="battery",
        name="Battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "lock_state": SensorEntityDescription(
        key="lock_state",
        name="Lock state",
        icon="mdi:lock",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "door_sensor_state": SensorEntityDescription(
        key="door_state",
        name="Door state",
        icon="mdi:door",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "last_lock_action": SensorEntityDescription(
        key="last_lock_action",
        name="Last lock action",
        icon="mdi:door",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "last_lock_action_trigger": SensorEntityDescription(
        key="last_lock_action_trigger",
        name="Last Action Trigger",
        icon="mdi:door",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "last_lock_action_completion_status": SensorEntityDescription(
        key="last_lock_action_completion_status",
        name="Last action completion status",
        icon="mdi:door",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "nuki_state": SensorEntityDescription(
        key="nuki_state",
        name="Nuki state",
        icon="mdi:lock",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "firmware_version": SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "hardware_revision": SensorEntityDescription(
        key="hardware_revision",
        name="Hardware Revision",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nuki sensor based on a config entry."""
    coordinator: NukiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    # entities = [NukiSensor(coordinator, sensor) for sensor in SENSOR_TYPES]
    entities = [
        NukiSensor(coordinator, sensor, coordinator.device.get_keyturner_state)
        for sensor in SENSOR_TYPES
        if sensor in coordinator.device.get_keyturner_state()
    ]
    # entities.extend(
    #     NukiSensor(coordinator, sensor, coordinator.device.get_config)
    #     for sensor in SENSOR_TYPES
    #     if sensor in coordinator.device.get_config()
    # )
    entities.append(NukiRSSISensor(coordinator, "rssi"))
    entities.append(NukiBatterySensor(coordinator, "battery"))
    entities.append(NukiVarsionInfo(coordinator, "firmware_version"))
    entities.append(NukiVarsionInfo(coordinator, "hardware_revision"))
    async_add_entities(entities)


class NukiSensor(NukiEntity, SensorEntity):
    """Representation of a Nuki sensor."""

    def __init__(
        self, coordinator: NukiDataUpdateCoordinator, sensor: str, info_function=None
    ) -> None:
        """Initialize the Niki sensor."""
        super().__init__(coordinator)
        self._sensor = sensor
        self._attr_unique_id = f"{coordinator.base_unique_id}-{sensor}"
        self.entity_description = SENSOR_TYPES[sensor]
        self._info_function = info_function

    @property
    def native_value(self) -> str | int | None:
        # """Return the state of the sensor."""
        return self._info_function()[self._sensor]


class NukiVarsionInfo(NukiSensor):
    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        return ".".join(str(x) for x in self._device.get_config()[self._sensor])


class NukiBatterySensor(NukiSensor):
    """Representation of a Nuki Battery sensor."""

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        return self._device.battery_percentage


class NukiRSSISensor(NukiSensor):
    """Representation of a Nuki RSSI sensor."""

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        return self._device.rssi
