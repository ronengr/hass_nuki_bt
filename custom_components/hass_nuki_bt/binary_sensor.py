"""Support for Nuki binary sensors."""
from dataclasses import dataclass
from collections.abc import Callable
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.entity import EntityCategory

from pyNukiBT import NukiConst

from .const import DOMAIN
from .entity import NukiEntity
from .coordinator import NukiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class NukiBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes nuki sensor entities."""

    info_function: Callable | None = (
        lambda slf: slf.device.keyturner_state[slf.sensor] != 0
    )

SENSOR_TYPES_COMMON: list[NukiBinarySensorEntityDescription] = [
    NukiBinarySensorEntityDescription(
        key="battery_critical",
        name="Battery Critical",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        info_function=lambda slf: slf.device.is_battery_critical,
    ),
    NukiBinarySensorEntityDescription(
        key="battery_charging",
        name="Battery Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        entity_category=EntityCategory.DIAGNOSTIC,
        info_function=lambda slf: slf.device.is_battery_charging,
    ),
]
SENSOR_TYPES_OPENER: list[NukiBinarySensorEntityDescription] = SENSOR_TYPES_COMMON
SENSOR_TYPES_LOCK: list[NukiBinarySensorEntityDescription] = [
    NukiBinarySensorEntityDescription(
        key="accessory_battery_state",
        name="Keypad Battery Critical",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        info_function=lambda slf: slf.device.keyturner_state[slf.sensor] & 0x2,
    ),
    NukiBinarySensorEntityDescription(
        key="nightmode_active",
        name="Night Mode",
        device_class="night_mode",
        icon="hass:weather-night",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    NukiBinarySensorEntityDescription(
        key="was_autounlock",
        name="Last action was autounlock",
        entity_category=EntityCategory.DIAGNOSTIC,
        info_function=lambda slf: flags & 0x1 == 1 if ((data:=slf.coordinator.last_nuki_log_entry.get("data")) and (flags := data.get("flags"))) \
            else False,
        entity_registry_enabled_default=False,
    ),
]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Nuki sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.device.device_type == NukiConst.NukiDeviceType.OPENER:
        async_add_entities([NukiBinarySensor(coordinator, sensor) for sensor in SENSOR_TYPES_OPENER])
    else:
        async_add_entities([NukiBinarySensor(coordinator, sensor) for sensor in SENSOR_TYPES_LOCK])
    return True


class NukiBinarySensor(NukiEntity, BinarySensorEntity):
    """Representation of a Nuki sensor."""

    def __init__(self, coordinator: NukiDataUpdateCoordinator, sensor: NukiBinarySensorEntityDescription) -> None:
        """Initialize the Niki sensor."""
        super().__init__(coordinator)
        self._attr_name = sensor.name
        self._attr_unique_id = f"{coordinator.base_unique_id}-{sensor.key}"
        self._info_function = self.entity_description.info_function
        self._async_update_attrs()

    def _async_update_attrs(self) -> None:
        """Update the entity attributes."""
        self._attr_is_on = self._info_function(self)
