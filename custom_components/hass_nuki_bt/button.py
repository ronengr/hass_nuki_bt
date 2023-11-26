"""Button platform for hass_nuki_bt."""
from dataclasses import dataclass
import logging
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyNukiBT import NukiDevice, NukiLockConst

from .entity import NukiEntity

from .coordinator import NukiDataUpdateCoordinator
from .const import DOMAIN


logger = logging.getLogger(__name__)


@dataclass
class NukiButtonEntityDescription(ButtonEntityDescription):
    """A class that describes nuki button entities."""

    action: NukiLockConst.LockAction = None


BUTTON_TYPES: [NukiButtonEntityDescription] = (
    NukiButtonEntityDescription(
        key="battery_critical", name="Unlatch", action=NukiLockConst.LockAction.UNLATCH
    ),
    NukiButtonEntityDescription(
        name="Lock 'n' Go", key="lockngo", action=NukiLockConst.LockAction.LOCK_N_GO
    ),
    NukiButtonEntityDescription(
        name="Lock 'n' Go with unlatch",
        key="lockngounlatch",
        action=NukiLockConst.LockAction.LOCK_N_GO_UNLATCH,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nuki lock based on a config entry."""
    coordinator: NukiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NukiButton(coordinator, btn) for btn in BUTTON_TYPES])


class NukiButton(ButtonEntity, NukiEntity):
    """Buttons for the Nuki lock."""

    _device: NukiDevice

    def __init__(
        self, coordinator: NukiDataUpdateCoordinator, btn: NukiButtonEntityDescription
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_name = btn.name
        self._attr_unique_id = f"{coordinator.base_unique_id}-{btn.key}"
        self._action = btn.action

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.async_lock_action(self._action)
