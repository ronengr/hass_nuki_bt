"""Library to handle connection with Nuki Lock."""
import logging
import voluptuous as vol
from typing import Any
from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from pyNukiBT import NukiConst, NukiDevice, NukiLockConst, NukiOpenerConst

from .entity import NukiEntity

from .coordinator import NukiDataUpdateCoordinator
from .const import DOMAIN

logger = logging.getLogger(__name__)

UPDATE_NUKI_TIME_SERVICE_NAME = "update_nuki_time"
# Has to be a simple dictionary to be extended with "target" parameters.
UPDATE_NUKI_TIME_SCHEMA = {
    vol.Optional("time"): cv.datetime,
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: entity_platform.AddEntitiesCallback
) -> None:
    """Set up Nuki lock based on a config entry."""
    coordinator: NukiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.device.device_type == NukiConst.NukiDeviceType.OPENER:
        async_add_entities([NukiOpener(coordinator)])
    else:
        async_add_entities([NukiLock(coordinator)])
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        UPDATE_NUKI_TIME_SERVICE_NAME,
        schema=UPDATE_NUKI_TIME_SCHEMA,
        func="async_handle_update_nuki_time",
        supports_response=SupportsResponse.OPTIONAL,
    )


class NukiLock(NukiEntity, LockEntity):
    """Representation of a Nuki lock."""

    _device: NukiDevice

    def __init__(self, coordinator: NukiDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_name = "Lock"
        self._attr_unique_id = f"{coordinator.base_unique_id}-lock"
        self._attr_supported_features = LockEntityFeature.OPEN
        self._async_update_attrs()

    def _async_update_attrs(self) -> None:
        """Update the entity attributes."""
        status = self.device.keyturner_state.lock_state
        self._attr_is_jammed = status is NukiLockConst.LockState.MOTOR_BLOCKED
        self._attr_is_open = status is NukiOpenerConst.LockState.OPEN
        self._attr_is_opening = status is  NukiOpenerConst.LockState.OPENING
        self._attr_is_locked = status is NukiLockConst.LockState.LOCKED
        self._attr_is_locking = status is NukiLockConst.LockState.LOCKING
        self._attr_is_unlocking = status is NukiLockConst.LockState.UNLOCKING

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        await self.async_lock_action(NukiLockConst.LockAction.LOCK)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        await self.async_lock_action(NukiLockConst.LockAction.UNLOCK)

    async def async_open(self, **kwargs: Any) -> None:
        """Open the door latch."""
        await self.async_lock_action(NukiLockConst.LockAction.UNLATCH)

class NukiOpener(NukiEntity, LockEntity):
    """Representation of a Nuki lock."""

    _device: NukiDevice

    def __init__(self, coordinator: NukiDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_name = "Lock"
        self._attr_unique_id = f"{coordinator.base_unique_id}-lock"
        self._attr_supported_features = LockEntityFeature.OPEN
        self._async_update_attrs()

    def _async_update_attrs(self) -> None:
        """Update the entity attributes."""
        status = self.device.keyturner_state.lock_state
        self._attr_is_jammed = status is NukiOpenerConst.LockState.UNCALIBRATED
        self._attr_is_open = status is NukiOpenerConst.LockState.OPEN
        self._attr_is_opening = status is NukiOpenerConst.LockState.OPENING
        self._attr_is_locked = status is NukiOpenerConst.LockState.LOCKED
        self._attr_is_unknown = status is NukiOpenerConst.LockState.UNDEFINED

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        await self.async_lock_action(NukiOpenerConst.LockAction.DEACTIVATE_RTO)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        await self.async_lock_action(NukiOpenerConst.LockAction.ACTIVATE_RTO)

    async def async_open(self, **kwargs: Any) -> None:
        """Open the door latch."""
        await self.async_lock_action(NukiOpenerConst.LockAction.ELECTRIC_STRIKE_ACTUATION)
