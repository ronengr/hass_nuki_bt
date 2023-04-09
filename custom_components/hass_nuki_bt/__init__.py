"""Custom integration to integrate hass_nuki_bt with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/hass_nuki_bt
"""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components import bluetooth
from homeassistant.exceptions import ConfigEntryNotReady

from .nuki import NukiDevice
from .api import IntegrationBlueprintApiClient
from .const import (
    CONF_APP_ID,
    CONF_AUTH_ID,
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_PUBLIC_KEY,
    CONF_PRIVATE_KEY,
    CONF_PUBLIC_KEY,
    DOMAIN,
    NukiConst,
)
from .coordinator import BlueprintDataUpdateCoordinator, NukiDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.LOCK,
]

_LOGGER = logging.getLogger(__name__)


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    address: str = entry.data[CONF_DEVICE_ADDRESS]

    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), connectable=False
    )
    if not ble_device:
        raise ConfigEntryNotReady(f"Could not find Nuki with address {address}")

    device = NukiDevice(
        address=entry.data[CONF_DEVICE_ADDRESS],
        auth_id=bytes.fromhex(entry.data[CONF_AUTH_ID]),
        nuki_public_key=bytes.fromhex(entry.data[CONF_DEVICE_PUBLIC_KEY]),
        bridge_public_key=bytes.fromhex(entry.data[CONF_PUBLIC_KEY]),
        bridge_private_key=bytes.fromhex(entry.data[CONF_PRIVATE_KEY]),
        app_id=2324564706,  # entry.data[CONF_APP_ID],
        ble_device=ble_device,
        model=NukiConst.NukiDeviceType.SMARTLOCK_1_2,  # lock or opener
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator = NukiDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        ble_device=ble_device,
        device=device,
        base_unique_id=entry.unique_id,
        model=NukiConst.NukiDeviceType.SMARTLOCK_1_2,
        connectable=True,
    )

    await device.update_state()
    entry.async_on_unload(coordinator.async_start())
    if not await coordinator.async_wait_ready():
        raise ConfigEntryNotReady(f"{address} is not advertising state")

    # entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    # await hass.config_entries.async_forward_entry_setups(
    #     entry, PLATFORMS_BY_TYPE[sensor_type]
    # )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    # await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
