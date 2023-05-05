"""Library to handle connection with Nuki Lock."""
import logging
from typing import Any
from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyNukiBT import NukiDevice, NukiLockConst, NukiErrorException

from .entity import NukiEntity

from .coordinator import NukiDataUpdateCoordinator
from .const import DOMAIN

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nuki lock based on a config entry."""
    coordinator: NukiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([(NukiLock(coordinator))])


# noinspection PyAbstractClass
class NukiLock(NukiEntity, LockEntity):
    """Representation of a Nuki lock."""

    _device: NukiDevice

    def __init__(self, coordinator: NukiDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_name = "Lock"
        self._attr_unique_id = f"{coordinator.base_unique_id}-lock"
        self._attr_supported_features = LockEntityFeature.OPEN
        self._last_result = None
        self._async_update_attrs()

    def _async_update_attrs(self) -> None:
        """Update the entity attributes."""
        status = self.device.keyturner_state.lock_state
        self._attr_is_locked = status is NukiLockConst.LockState.LOCKED
        self._attr_is_locking = status is NukiLockConst.LockState.LOCKING
        self._attr_is_unlocking = status is NukiLockConst.LockState.UNLOCKING
        self._attr_is_jammed = status is NukiLockConst.LockState.MOTOR_BLOCKED

    async def async_lock_action(self, action):
        """Do door action."""
        try:
            user = await self.hass.auth.async_get_user(self._context.user_id)
            msg = await self.device.lock_action(action, name_suffix=user.name)
        except NukiErrorException as ex:
            self._last_run_success = False
            self._last_result = ex.error_code
        else:
            self._last_run_success = True
            self._last_result = msg.status
        self.async_write_ha_state()

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        await self.async_lock_action(NukiLockConst.LockAction.LOCK)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        await self.async_lock_action(NukiLockConst.LockAction.UNLOCK)

    async def async_open(self, **kwargs: Any) -> None:
        """Open the door latch."""
        await self.async_lock_action(NukiLockConst.LockAction.UNLATCH)
