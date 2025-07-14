"""DataUpdateCoordinator for hass_nuki_bt."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

import async_timeout

from bleak import BleakError

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.active_update_coordinator import (
    ActiveBluetoothDataUpdateCoordinator,
)
from homeassistant.core import HomeAssistant, callback
from pyNukiBT import NukiDevice, NukiConst

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)

DEVICE_STARTUP_TIMEOUT = 300


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

    async def async_get_last_action_log_entry(self):
        """Get the last action log entry."""
        if self._security_pin:
            # get the latest log entry
            # todo: check if Nuki logging is enabled
            logs = await self.device.request_log_entries(
                security_pin=self._security_pin, count=1
            )
            if logs:
                if logs[0].type == NukiConst.LogEntryType.LOCK_ACTION:
                    # todo: handle other log types
                    self.last_nuki_log_entry = logs[0]
                elif logs[0].index > self.last_nuki_log_entry["index"]:
                    # if there are new log entries, get max 10 entries
                    logs = await self.device.request_log_entries(
                        security_pin=self._security_pin,
                        count=min(10, logs[0].index - self.last_nuki_log_entry["index"]),
                        start_index=logs[0].index,
                    )
                    for log in logs:
                        if log.type == NukiConst.LogEntryType.LOCK_ACTION:
                            self.last_nuki_log_entry = log
                            break

