from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)

from .coordinator import NukiDataUpdateCoordinator
from .const import DOMAIN, LockState
from .nuki import NukiDevice


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nuki lock based on a config entry."""
    coordinator: NukiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([(NukiLock(coordinator))])


# noinspection PyAbstractClass
class NukiLock(
    LockEntity, PassiveBluetoothCoordinatorEntity[NukiDataUpdateCoordinator]
):
    """Representation of a Nuki lock."""

    _device: NukiDevice

    def __init__(self, coordinator: NukiDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        self._last_run_success = None
        super().__init__(coordinator)
        self._async_update_attrs()

    def _async_update_attrs(self) -> None:
        """Update the entity attributes."""
        status = self._device.keyturner_state.lock_state
        self._attr_is_locked = status is LockState.LOCKED
        self._attr_is_locking = status is LockState.LOCKING
        self._attr_is_unlocking = status is LockState.UNLOCKING
        self._attr_is_jammed = status is LockState.MOTOR_BLOCKED

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        self._last_run_success = await self._device.lock()
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        self._last_run_success = await self._device.unlock()
        self.async_write_ha_state()
