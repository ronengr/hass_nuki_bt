"""NukiEntity class."""
from __future__ import annotations

import logging

from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.core import callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from pyNukiBT import NukiDevice

from .const import MANUFACTURER
from .coordinator import NukiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class NukiEntity(PassiveBluetoothCoordinatorEntity[NukiDataUpdateCoordinator]):
    """Generic entity encapsulating common features of Nuki device."""

    device: NukiDevice
    _attr_has_entity_name = True

    def __init__(self, coordinator: NukiDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.device = coordinator.device
        self._address = coordinator.ble_device.address
        self._attr_unique_id = coordinator.base_unique_id
        self._attr_device_info = DeviceInfo(
            connections={(dr.CONNECTION_BLUETOOTH, self._address)},
            manufacturer=MANUFACTURER,
            model=coordinator.device.device_type,
            name=coordinator.device_name,
            hw_version=".".join(
                str(x) for x in coordinator.device.config.get("hardware_revision",[])
            ),
            sw_version=".".join(
                str(x) for x in coordinator.device.config.get("firmware_version",[])
            ),
        )

    @callback
    def _async_update_attrs(self) -> None:
        """Update the entity attributes."""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
        return await super().async_added_to_hass()

    async def async_lock_action(self, action):
        """Do door action."""
        user = await self.hass.auth.async_get_user(self._context.user_id)
        user_name = user.name if user else None
        await self.device.lock_action(action, name_suffix=user_name, wait_for_completed = True)
        await self.coordinator.async_get_last_action_log_entry()
        self.coordinator.async_update_listeners()

    async def async_handle_update_nuki_time(self, time=None):
        """Update nuki time."""
        if self.coordinator._security_pin is None: #security pin can be 0, so check for None
            raise ServiceValidationError("Security PIN is required to update nuki time.")
        result = await self.device.update_nuki_time(self.coordinator._security_pin, time)
        return result.status
