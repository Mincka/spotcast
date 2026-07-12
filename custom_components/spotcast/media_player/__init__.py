"""Module to manage types of media_player compatible with spotcast

Classes:
    - Chromecast
    - SpotifyDevice
    - MediaPlayer
    - DeviceManager

Functions:
    - async_setup_entry
"""
from logging import getLogger

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.spotcast.const import DOMAIN
from custom_components.spotcast.media_player.chromecast_player import (
    Chromecast,
)
from custom_components.spotcast.media_player._abstract_player import (
    MediaPlayer
)
from custom_components.spotcast.media_player.spotify_player import (
    SpotifyDevice
)
from custom_components.spotcast.media_player.device_manager import (
    DeviceManager
)
from custom_components.spotcast.spotify import SpotifyAccount

LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setups media player for Spotcast"""

    account = await SpotifyAccount.async_from_config_entry(hass, entry)
    device_manager = DeviceManager(account, async_add_entities)

    # register the device manager so the account coordinator drives
    # its updates
    entry_data = hass.data.setdefault(DOMAIN, {}).setdefault(
        entry.entry_id,
        {},
    )
    entry_data["device_manager"] = device_manager

    await device_manager.async_update()
