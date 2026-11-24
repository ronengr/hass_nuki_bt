"""DataUpdateCoordinator for hass_nuki_bt."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import async_timeout

from bleak import BleakError

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.active_update_coordinator import (
    ActiveBluetoothDataUpdateCoordinator,
)
from homeassistant.core import HomeAssistant, callback
from pyNukiBT import NukiDevice, NukiConst

from .const import RING_BUS_EVENT, RING_EVENT_RING, RING_EVENT_RING_LOCKED

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)

DEVICE_STARTUP_TIMEOUT = 300

LOCK_LOG_TYPES = [NukiConst.LogEntryType.LOCK_ACTION, NukiConst.LogEntryType.KEYPAD_ACTION]


class NukiDataUpdateCoordinator(ActiveBluetoothDataUpdateCoordinator[None]):
    """Class to manage fetching Nuki data."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        ble_device: BLEDevice,
        device: NukiDevice,
        base_unique_id: str,
        device_name: str,
        connectable: bool,
        security_pin: int = None,
    ) -> None:
        """Initialize global nuki data updater."""
        super().__init__(
            hass=hass,
            logger=logger,
            address=ble_device.address,
            needs_poll_method=self._needs_poll,
            poll_method=self._async_update,
            mode=bluetooth.BluetoothScanningMode.PASSIVE,
            connectable=connectable,
        )
        self.ble_device = ble_device
        self.device = device
        self.device_name = device_name
        self.base_unique_id = base_unique_id
        self.model = None
        self.last_nuki_log_entry = {"index" : 0}
        self._security_pin = security_pin
        self._unsubscribe_nuki_callbacks = None
        self._last_seen_log_index: int | None = None
        self._ring_listeners: list[Callable[[dict], None]] = []
        self.last_ring: dict | None = None

    @callback
    def _async_start(self) -> None:
        self._unsubscribe_nuki_callbacks = self.device.subscribe(
            self._nuki_device_callback
        )
        return super()._async_start()

    @callback
    def _async_stop(self) -> None:
        if self._unsubscribe_nuki_callbacks is not None:
            self._unsubscribe_nuki_callbacks()
        return super()._async_stop()

    @callback
    def _nuki_device_callback(self, command: NukiConst.NukiCommand = None) -> None:
        self.async_update_listeners()

    @callback
    def _needs_poll(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        seconds_since_last_poll: float | None,
    ) -> bool:
        return self.device.poll_needed(seconds_since_last_poll)

    async def _async_update(
        self, service_info: bluetooth.BluetoothServiceInfoBleak = None
    ) -> None:
        """Poll the device."""
        if service_info:
            self.device.set_ble_device(service_info.device)
        await self.device.update_state()
        await self.async_get_last_action_log_entry()

    @callback
    def _async_handle_bluetooth_event(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Handle a Bluetooth event."""
        self.ble_device = service_info.device
        self.device.parse_advertisement_data(
            service_info.device, service_info.advertisement
        )
        super()._async_handle_bluetooth_event(service_info, change)

    async def async_wait_ready(self) -> bool:
        """Wait for the device to be ready."""
        with contextlib.suppress(asyncio.TimeoutError):
            async with async_timeout.timeout(DEVICE_STARTUP_TIMEOUT):
                try:
                    await self._async_update()
                except BleakError:
                    return False
                return True
        return False

    @callback
    def async_add_ring_listener(self, listener: Callable[[dict], None]) -> Callable[[], None]:
        """Register a listener that is called on every detected doorbell ring (Opener only)."""
        self._ring_listeners.append(listener)

        @callback
        def _remove() -> None:
            if listener in self._ring_listeners:
                self._ring_listeners.remove(listener)

        return _remove

    @callback
    def _async_handle_doorbell_log(self, log) -> None:
        """Handle an Opener 'Doorbell recognition' log entry (type 0x06).

        According to the Nuki Opener BLE API, byte 1 of the log data is a bitmask:
        bit 0 = Ring to Open active, bit 1 = Continuous Mode active.
        pyNukiBT parses log type 0x06 with the Smart Lock door sensor structure, so this
        byte ends up in the field 'door_status'.
        """
        data = log.get("data") or {}
        mode_bits = int(data.get("door_status", 0) or 0) & 0x03
        rto_active = bool(mode_bits & 0x01)
        cm_active = bool(mode_bits & 0x02)
        event_type = RING_EVENT_RING if (rto_active or cm_active) else RING_EVENT_RING_LOCKED
        timestamp = log.get("timestamp")
        ring = {
            "type": event_type,
            "ring_to_open_active": rto_active,
            "continuous_mode_active": cm_active,
            "log_index": int(log.get("index", 0)),
            "log_timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else None,
        }
        _LOGGER.debug("%s: doorbell ring detected: %s", self.device_name, ring)
        self.last_ring = ring
        self.hass.bus.async_fire(
            RING_BUS_EVENT,
            {"name": self.device_name, "address": self.ble_device.address, **ring},
        )
        for listener in list(self._ring_listeners):
            listener(ring)

    async def async_get_last_action_log_entry(self):
        """Fetch new log entries.

        Keeps track of the last lock/keypad action (for the existing sensors) and
        detects doorbell rings on the Nuki Opener.
        """
        if self._security_pin is None:  # security pin can be 0, so check for None
            return
        # todo: check if Nuki logging is enabled
        logs = await self.device.request_log_entries(
            security_pin=self._security_pin, count=1
        )
        if not logs:
            return
        newest = logs[0]
        newest_index = int(newest.index)

        if self._last_seen_log_index is None:
            # First run after start: only remember where we are, don't report old rings.
            self._last_seen_log_index = newest_index
            if newest.type in LOCK_LOG_TYPES:
                self.last_nuki_log_entry = newest
            elif newest_index > 0:
                logs = await self.device.request_log_entries(
                    security_pin=self._security_pin,
                    count=min(10, newest_index),
                    start_index=newest_index,
                )
                for log in logs:
                    if log.type in LOCK_LOG_TYPES:
                        self.last_nuki_log_entry = log
                        break
            return

        new_count = newest_index - self._last_seen_log_index
        if new_count <= 0:
            if new_count < 0:
                # Log was cleared / counter reset on the device.
                self._last_seen_log_index = newest_index
            return

        if new_count > 1:
            # Logs are returned newest first (sort order descending)
            logs = await self.device.request_log_entries(
                security_pin=self._security_pin,
                count=min(10, new_count),
                start_index=newest_index,
            )
        # Keep each log index only once: the BLE notifications can arrive more than once,
        # which would otherwise report the same ring several times.
        new_logs = []
        seen_indexes = set()
        for log in logs:
            index = int(log.index)
            if index > self._last_seen_log_index and index not in seen_indexes:
                seen_indexes.add(index)
                new_logs.append(log)
        self._last_seen_log_index = newest_index

        for log in new_logs:
            if log.type in LOCK_LOG_TYPES:
                self.last_nuki_log_entry = log
                break

        if self.device.device_type == NukiConst.NukiDeviceType.OPENER:
            # oldest first, so multiple rings are reported in the right order
            for log in reversed(new_logs):
                if log.type == NukiConst.LogEntryType.DOOR_SENSOR:  # = DOORBELL_RECOGNITION on the Opener
                    self._async_handle_doorbell_log(log)
