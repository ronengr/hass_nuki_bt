"""Library to handle connection with Nuki Lock."""
import logging
from typing import Any
from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyNukiBT import NukiDevice, NukiLockConst

from .entity import NukiEntity

from .coordinator import NukiDataUpdateCoordinator
from .const import DOMAIN

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nuki lock based on a config entry."""
    coordinator: NukiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NukiLock(coordinator)])


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
        self._attr_is_locked = status is NukiLockConst.LockState.LOCKED
        self._attr_is_locking = status is NukiLockConst.LockState.LOCKING
        self._attr_is_unlocking = status is NukiLockConst.LockState.UNLOCKING
        self._attr_is_jammed = status is NukiLockConst.LockState.MOTOR_BLOCKED

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        await self.async_lock_action(NukiLockConst.LockAction.LOCK)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        await self.async_lock_action(NukiLockConst.LockAction.UNLOCK)

    async def async_open(self, **kwargs: Any) -> None:
        """Open the door latch."""
        await self.async_lock_action(NukiLockConst.LockAction.UNLATCH)
