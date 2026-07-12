"""Module for the Spotcast data update coordinator.

Classes:
    - SpotcastCoordinator

Constants:
    - ENTITY_SPECIFIC_ERRORS(tuple): errors specific to entity
        updates that must be handled gracefully
    - POTENTIAL_ERRORS(tuple): all the errors that can be raised
        while communicating with the Spotify API
    - UPDATE_ERRORS(tuple): the errors converted to an UpdateFailed
        during a coordinator refresh
"""

from asyncio import exceptions as asyncio_errors
from datetime import timedelta
from logging import getLogger

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from requests import exceptions as requests_errors
from spotipy import SpotifyException

from custom_components.spotcast.const import DOMAIN
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.sessions.exceptions import TokenError
from custom_components.spotcast.sessions.retry_supervisor import (
    RetrySupervisor,
)

LOGGER = getLogger(__name__)

ENTITY_SPECIFIC_ERRORS = (
    TokenError,
    requests_errors.RetryError,
    asyncio_errors.TimeoutError,
)
POTENTIAL_ERRORS = (
    RetrySupervisor.SUPERVISED_EXCEPTIONS + ENTITY_SPECIFIC_ERRORS
)
UPDATE_ERRORS = POTENTIAL_ERRORS + (SpotifyException,)


class SpotcastCoordinator(DataUpdateCoordinator[dict]):
    """Data update coordinator for a Spotcast account.

    Refreshes the fast lane data of a Spotify account (profile,
    devices, playback state and library counts) in a single burst per
    update interval. The account datasets remain an inner cache and
    api throttling layer.

    Attributes:
        - account(SpotifyAccount): the Spotify account refreshed by
            the coordinator

    Methods:
        - _async_update_data
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        account: SpotifyAccount,
    ):
        """Data update coordinator for a Spotcast account.

        Args:
            - hass(HomeAssistant): The Home Assistant Instance
            - entry(ConfigEntry): The config entry of the account
            - account(SpotifyAccount): The Spotify account refreshed
                by the coordinator
        """
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=account.base_refresh_rate),
        )
        self.account = account

    async def _async_update_data(self) -> dict:
        """Refreshes the fast lane data for the account.

        Raises:
            - UpdateFailed: raised when the Spotify API could not be
                reached or replied with an error

        Returns:
            - dict: the refreshed profile, devices, playback state
                and library counts for the account
        """
        LOGGER.debug(
            "Refreshing coordinator data for entry `%s`",
            self.account.entry_id,
        )

        try:
            profile = await self.account.async_profile()
            devices = await self.account.async_devices()
            playback_state = await self.account.async_playback_state()
            playlists_count = await self.account.async_playlists_count()
            liked_songs_count = await self.account.async_liked_songs_count()
        except UPDATE_ERRORS as exc:
            raise UpdateFailed(
                "Could not refresh Spotify data for entry "
                f"`{self.account.entry_id}`: {exc}"
            ) from exc

        await self._async_update_device_manager()

        return {
            "profile": profile,
            "devices": devices,
            "playback_state": playback_state,
            "playlists_count": playlists_count,
            "liked_songs_count": liked_songs_count,
        }

    async def _async_update_device_manager(self):
        """Runs the device manager update if one was registered."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(
            self.config_entry.entry_id,
            {},
        )

        device_manager = entry_data.get("device_manager")

        if device_manager is None:
            LOGGER.debug(
                "No device manager registered for entry `%s`. Skipping",
                self.config_entry.entry_id,
            )
            return

        await device_manager.async_update()
