"""Adds config flow for Blueprint."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_DEVICE_ID,
)
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    IntegrationBlueprintApiClient,
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientCommunicationError,
    IntegrationBlueprintApiClientError,
)
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


class BlueprintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except IntegrationBlueprintApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except IntegrationBlueprintApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except IntegrationBlueprintApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_ADDRESS,
                        description="Device Address",
                        default=(user_input or {}).get(CONF_DEVICE_ADDRESS),
                    ): str,
                    vol.Required(
                        CONF_DEVICE_ID,
                        description="Device ID",
                        default=(user_input or {}).get(CONF_DEVICE_ID),
                    ): str,
                    vol.Required(
                        CONF_AUTH_ID,
                        description="Auth ID",
                        default=(user_input or {}).get(CONF_AUTH_ID),
                    ): str,
                    vol.Required(
                        CONF_PRIVATE_KEY,
                        description="Private key",
                        default=(user_input or {}).get(CONF_PRIVATE_KEY),
                    ): str,
                    vol.Required(
                        CONF_PUBLIC_KEY,
                        description="Public key",
                        default=(user_input or {}).get(CONF_PUBLIC_KEY),
                    ): str,
                    vol.Required(
                        CONF_DEVICE_PUBLIC_KEY,
                        description="Device public key",
                        default=(user_input or {}).get(CONF_DEVICE_PUBLIC_KEY),
                    ): str,
                    vol.Required(
                        CONF_APP_ID,
                        description="Public key",
                        default=(user_input or {}).get(CONF_APP_ID),
                    ): str,
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def _test_credentials(self, username: str, password: str) -> None:
        """Validate credentials."""
        client = IntegrationBlueprintApiClient(
            username=username,
            password=password,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_data()
