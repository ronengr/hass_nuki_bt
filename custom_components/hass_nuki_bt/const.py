"""Constants for hass_nuki_bt."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "Nuki BT"
DOMAIN = "hass_nuki_bt"
MANUFACTURER = "nuki"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

# config
CONF_DEVICE_ADDRESS = "device_address"
CONF_AUTH_ID = "auth_id"
CONF_PRIVATE_KEY = "private_key"
CONF_PUBLIC_KEY = "public_key"
CONF_DEVICE_PUBLIC_KEY = "device_public_key"
CONF_APP_ID = "app_id"
CONF_CLIENT_TYPE = "client_type"
