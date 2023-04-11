"""Adds config flow for Nuki."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    CONF_APP_ID,
    CONF_AUTH_ID,
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_PUBLIC_KEY,
    CONF_PRIVATE_KEY,
    CONF_PUBLIC_KEY,
    DOMAIN,
    LOGGER,
)


class NukiFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Nuki."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                LOGGER.debug("got user input")
                # todo: validate input
            except Exception as ex:
                LOGGER.debug(f"got exception {ex}")
            else:
                return self.async_create_entry(
                    title=user_input[CONF_DEVICE_ID],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_ADDRESS,
                        # description="Device Address",
                    ): str,
                    vol.Optional(
                        CONF_DEVICE_ID,
                        # description="Device ID",
                        # default=(user_input or {}).get(CONF_DEVICE_ID),
                    ): str,
                    vol.Required(
                        CONF_AUTH_ID,
                        # description="Auth ID",
                        # default=(user_input or {}).get(CONF_AUTH_ID),
                    ): str,
                    vol.Required(
                        CONF_PRIVATE_KEY,
                        # description="Private key",
                        # default=(user_input or {}).get(CONF_PRIVATE_KEY),
                    ): str,
                    vol.Required(
                        CONF_PUBLIC_KEY,
                        # description="Public key",
                        # default=(user_input or {}).get(CONF_PUBLIC_KEY),
                    ): str,
                    vol.Required(
                        CONF_DEVICE_PUBLIC_KEY,
                        # description="Device public key",
                        # default=(user_input or {}).get(CONF_DEVICE_PUBLIC_KEY),
                    ): str,
                    vol.Required(
                        CONF_APP_ID,
                        # description="Public key",
                        # default=(user_input or {}).get(CONF_APP_ID),
                    ): str,
                }
            ),
            errors=_errors,
        )
