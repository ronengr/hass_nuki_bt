from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import EntityCategory

import logging

from .const import DOMAIN, NukiLockConst
from .entity import NukiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.warning("addindg binary sensors")
    entities = []
    # data = entry.as_dict()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities.append(BatteryLow(coordinator))
    entities.append(BatteryCharging(coordinator))
    # entities.append(LockState(coordinator))
    # entities.append(KeypadBatteryLow(coordinator))
    # entities.append(RingAction(coordinator))
    entities.append(DoorState(coordinator))
    async_add_entities(entities)
    return True


class BatteryLow(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-battery_critical"
        self._attr_name = "Battery Critical"

    @property
    def is_on(self) -> bool:
        return self._device.is_battery_critical

    @property
    def device_class(self) -> str:
        return "battery"

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class BatteryCharging(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-battery_charging"
        self._attr_name = "Battery Charging"
        self._attr_device_class = "battery_charging"

    @property
    def is_on(self) -> bool:
        return self._device.is_battery_charging

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


# class KeypadBatteryLow(NukiEntity, BinarySensorEntity):
#     def __init__(self, coordinator):
#         super().__init__(coordinator)
#         self.set_id("binary_sensor", "keypad_battery_low")
#         self.set_name("Keypad Battery Critical")

#     @property
#     def is_on(self) -> bool:
#         return self.last_state.get("keypadBatteryCritical", False)

#     @property
#     def device_class(self) -> str:
#         return "battery"

#     @property
#     def entity_category(self):
#         return EntityCategory.DIAGNOSTIC


# class RingAction(NukiEntity, BinarySensorEntity):
#     def __init__(self, coordinator):
#         super().__init__(coordinator)
#         self.set_id("binary_sensor", "ring_action")
#         self.set_name("Ring Action")

#     @property
#     def is_on(self) -> bool:
#         return self.last_state.get("ringactionState", False)

#     @property
#     def extra_state_attributes(self):
#         return {"timestamp": self.last_state.get("ringactionTimestamp")}

#     @property
#     def entity_category(self):
#         return EntityCategory.DIAGNOSTIC


# class LockState(NukiEntity, BinarySensorEntity):
#     def __init__(self, coordinator):
#         super().__init__(coordinator)
#         self.set_id("binary_sensor", "state")
#         self.set_name("Locked")
#         self._attr_device_class = "lock"

#     @property
#     def is_on(self) -> bool:
#         current = LockStates(self.last_state.get("state", LockStates.UNDEFINED.value))
#         return current != LockStates.LOCKED

#     @property
#     def extra_state_attributes(self):
#         return {"timestamp": self.last_state.get("timestamp")}


class DoorState(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-door_state"
        self._attr_name = "Door Open"
        self._attr_device_class = "door"

    @property
    def is_on(self) -> bool:
        current = self._device.last_state.get(
            "door_sensor_state", NukiLockConst.DoorsensorState.UNKOWN
        )
        return current != NukiLockConst.DoorsensorState.DOOR_CLOSED
