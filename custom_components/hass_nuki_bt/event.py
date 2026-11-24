"""Doorbell ring event for the Nuki Opener."""
from __future__ import annotations

from homeassistant.components.event import (
    EventDeviceClass,
    EventEntity,
)
from homeassistant.core import callback

from pyNukiBT import NukiConst

from .const import DOMAIN, RING_EVENT_RING, RING_EVENT_RING_LOCKED
from .coordinator import NukiDataUpdateCoordinator
from .entity import NukiEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the ring event entity (Opener only)."""
    coordinator: NukiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.device.device_type == NukiConst.NukiDeviceType.OPENER:
        async_add_entities([NukiRingEvent(coordinator)])
    return True


class NukiRingEvent(NukiEntity, EventEntity):
    """Fires when someone rings the doorbell connected to the Nuki Opener.

    event_type "ring":       Ring to Open or Continuous Mode was active (door was opened)
    event_type "ringlocked": the Opener was locked, the door was not opened
    """

    _attr_device_class = EventDeviceClass.DOORBELL
    _attr_event_types = [RING_EVENT_RING, RING_EVENT_RING_LOCKED]
    _attr_icon = "mdi:doorbell"

    def __init__(self, coordinator: NukiDataUpdateCoordinator) -> None:
        """Initialize the ring event entity."""
        super().__init__(coordinator)
        self._attr_name = "Ring"
        self._attr_unique_id = f"{coordinator.base_unique_id}-ring_event"

    async def async_added_to_hass(self) -> None:
        """Register ring listener."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_ring_listener(self._async_handle_ring)
        )

    @callback
    def _async_handle_ring(self, ring: dict) -> None:
        """Handle a detected ring."""
        attributes = {key: value for key, value in ring.items() if key != "type"}
        self._trigger_event(ring["type"], attributes)
        self.async_write_ha_state()
