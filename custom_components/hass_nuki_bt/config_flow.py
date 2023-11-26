"""Adds config flow for Nuki."""
import random
from typing import Any
import re

from nacl.public import PrivateKey

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_NAME, CONF_PIN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from pyNukiBT import NukiConst, NukiDevice, NukiErrorException

from .const import (
    CONF_APP_ID,
    CONF_AUTH_ID,
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_PUBLIC_KEY,
    CONF_PRIVATE_KEY,
    CONF_PUBLIC_KEY,
    CONF_CLIENT_TYPE,
    DOMAIN,
    LOGGER,
)


class NukiFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Nuki."""

    VERSION = 1

    task_one = None
    task_two = None

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict = {}

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        LOGGER.info("Discovered bluetooth device: %s", discovery_info.as_dict())
        await self.async_set_unique_id(format_unique_id(discovery_info.address))
        self._abort_if_unique_id_configured()
        self._data[CONF_DEVICE_ADDRESS] = discovery_info.address.upper()
        self._data[CONF_NAME] = discovery_info.name
        self.context["title_placeholders"] = {
            "name": self._data[CONF_NAME],
            "address": self._data[CONF_DEVICE_ADDRESS],
        }

        return await self.async_step_step1()

    async def async_step_choose_method(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the chose method step."""
        return self.async_show_menu(
            step_id="choose_method",
            menu_options={"pair", "manual"},
            description_placeholders={
                "name": self._data[CONF_NAME],
                "address": self._data[CONF_DEVICE_ADDRESS],
            },
        )

    async def async_step_step1(
        self,
        user_input: dict | None = None,
    ) -> FlowResult:
        """Handle a flow."""
        if user_input:
            self._data |= user_input
        if (
            CONF_DEVICE_ADDRESS in self._data
            and validate_address(self._data[CONF_DEVICE_ADDRESS])
            and CONF_NAME in self._data
            and CONF_CLIENT_TYPE in self._data
        ):
            return await self.async_step_choose_method(user_input)
        return self.async_show_form(
            step_id="step1",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=self._data.get(CONF_NAME),
                    ): str,
                    vol.Required(
                        CONF_DEVICE_ADDRESS,
                        default=self._data.get(CONF_DEVICE_ADDRESS),
                    ): str,
                    vol.Optional(
                        CONF_PIN,
                    ): str,
                    vol.Required(CONF_CLIENT_TYPE, default="Bridge"): SelectSelector(
                        SelectSelectorConfig(
                            options=["Bridge", "App"],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> FlowResult:
        """Handle a user flow."""
        return await self.async_step_step1(user_input)

    async def async_step_pair(
        self,
        user_input: dict | None = None,
    ) -> FlowResult:
        """Handle a pairing flow."""
        if user_input:
            self._data |= user_input
        if CONF_CLIENT_TYPE not in self._data or CONF_DEVICE_ADDRESS not in self._data:
            return await self.async_step_step1(user_input)

        app_id = random.getrandbits(32)
        keypair = PrivateKey.generate()
        public_key = bytes(keypair.public_key)
        private_key = bytes(keypair)

        if self._data[CONF_CLIENT_TYPE] == "App":
            client_type = NukiConst.NukiClientType.APP
        else:
            client_type = NukiConst.NukiClientType.BRIDGE
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self._data[CONF_DEVICE_ADDRESS], connectable=True
        )

        device = NukiDevice(
            address=self._data[CONF_DEVICE_ADDRESS],
            auth_id=None,
            nuki_public_key=None,
            bridge_public_key=public_key,
            bridge_private_key=private_key,
            app_id=app_id,
            name="HomeAssistant",
            client_type=client_type,
            ble_device=ble_device,
            get_ble_device=lambda addr: bluetooth.async_ble_device_from_address(
                self.hass, addr, connectable=True
            ),
        )
        try:
            ret = await device.pair()
        except NukiErrorException as ex:
            LOGGER.error(ex)
            if ex.error_code == NukiConst.ErrorCode.P_ERROR_NOT_PAIRING:
                return self.async_show_form(
                    step_id="pair",
                    errors={"base": "pairing"},
                )

        self._data[CONF_AUTH_ID] = ret["auth_id"].hex()
        self._data[CONF_DEVICE_PUBLIC_KEY] = ret["nuki_public_key"].hex()
        self._data[CONF_PUBLIC_KEY] = public_key.hex()
        self._data[CONF_PRIVATE_KEY] = private_key.hex()
        self._data[CONF_APP_ID] = str(app_id)

        await device.disconnect()

        return self.async_create_entry(
            title=self._data[CONF_NAME],
            data=self._data,
        )

    async def async_step_manual(
        self,
        user_input: dict | None = None,
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input:
            self._data |= user_input
        if (
            CONF_CLIENT_TYPE in self._data
            and CONF_DEVICE_ADDRESS in self._data
            and CONF_AUTH_ID in self._data
            and CONF_PRIVATE_KEY in self._data
            and CONF_PRIVATE_KEY in self._data
            and CONF_PUBLIC_KEY in self._data
            and CONF_DEVICE_PUBLIC_KEY in self._data
        ):
            return self.async_create_entry(
                title=self._data[CONF_NAME],
                data=self._data,
            )
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_AUTH_ID,
                        default=self._data.get(CONF_AUTH_ID),
                    ): str,
                    vol.Required(
                        CONF_PRIVATE_KEY,
                        default=self._data.get(CONF_PRIVATE_KEY),
                    ): str,
                    vol.Required(
                        CONF_PUBLIC_KEY,
                        default=self._data.get(CONF_PUBLIC_KEY),
                    ): str,
                    vol.Required(
                        CONF_DEVICE_PUBLIC_KEY,
                        default=self._data.get(CONF_DEVICE_PUBLIC_KEY),
                    ): str,
                    vol.Required(
                        CONF_APP_ID,
                        default=self._data.get(CONF_APP_ID),
                    ): str,
                }
            ),
            errors=_errors,
        )


def format_unique_id(address: str) -> str:
    """Format the unique ID from address."""
    return address.replace(":", "").lower()


def validate_address(address: str) -> bool:
    """Validate address format."""
    r = re.compile("^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")
    return r.match(address) is not None
