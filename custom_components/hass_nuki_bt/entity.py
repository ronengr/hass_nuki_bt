"""NukiEntity class."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from pyNukiBT import NukiDevice

from .const import MANUFACTURER
from .coordinator import NukiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class NukiEntity(PassiveBluetoothCoordinatorEntity[NukiDataUpdateCoordinator]):
    """Generic entity encapsulating common features of Nuki device."""

    _device: NukiDevice
    _attr_has_entity_name = True

    def __init__(self, coordinator: NukiDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device = coordinator.device
        self._last_run_success: bool | None = None
        self._address = coordinator.ble_device.address
        self._attr_unique_id = coordinator.base_unique_id
        self._attr_device_info = DeviceInfo(
            connections={(dr.CONNECTION_BLUETOOTH, self._address)},
            manufacturer=MANUFACTURER,
            model=coordinator.device.device_type,
            name=coordinator.device_name,
            hw_version=".".join(
                str(x) for x in coordinator.device.config["hardware_revision"]
            ),
            sw_version=".".join(
                str(x) for x in coordinator.device.config["firmware_version"]
            ),
        )

    @property
    def extra_state_attributes(self) -> Mapping[Any, Any]:
        """Return the state attributes."""
        return {"last_run_success": self._last_run_success}

    # @callback
    # def _async_update_attrs(self) -> None:
    #     """Update the entity attributes."""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        # self._async_update_attrs()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(self._device.subscribe(self._handle_coordinator_update))
        return await super().async_added_to_hass()

    async def async_update(self) -> None:
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._device.update_state()
