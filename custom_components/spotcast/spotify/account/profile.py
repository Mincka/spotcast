"""Profile and identity information for the Spotify account.

Classes:
    ProfileMixin
"""

from logging import getLogger
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

from custom_components.spotcast.const import DOMAIN
from custom_components.spotcast.spotify.utils import select_image_url

LOGGER = getLogger(__name__)


class ProfileMixin:
    """Identity, profile, and account metadata for the account."""

    @property
    def id(self) -> str:
        """Returns the id of the account."""
        return self.get_profile_value("id")

    @property
    def name(self) -> str:
        """Returns the name of the account."""
        name = self.get_profile_value("display_name")

        if name is None:
            name = self.id

        return name

    @property
    def profile(self) -> dict:
        """Returns the full profile dictionary of the account."""
        return self.get_dataset("profile")

    @property
    def country(self) -> str:
        """Returns the current country in which the account resides."""
        return self.get_profile_value("country")

    @property
    def image_link(self) -> str:
        """Returns the link for the account profile image."""
        images = self.get_profile_value("images")
        return select_image_url(images)

    @property
    def product(self) -> str:
        """Returns the account subscription product."""
        return self.get_profile_value("product")

    @property
    def type(self) -> str:
        """Returns the type of account."""
        return self.get_profile_value("type")

    @property
    def liked_songs_uri(self) -> str:
        """Returns the liked songs uri for the account."""
        return f"spotify:user:{self.id}:collection"

    @property
    def device_info(self) -> DeviceInfo:
        """Returns the Home Assistant device info of the account."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.id)},
            manufacturer="Spotify AB",
            model=f"Spotify {self.profile['product']}",
            name=f"Spotcast {self.name}",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://open.spotify.com",
        )

    def get_profile_value(self, attribute: str) -> Any:
        """Returns the value for a profile element.

        Args:
            attribute(str): the attribute to fetch from the profile

        Returns:
            Any: the value at the key in the profile
        """
        profile = self._datasets["profile"].data

        return profile.get(attribute)

    async def async_profile(self, force: bool = False) -> dict:
        """Test the connection and returns a user profile.

        Args:
            force(bool, optional): Forces the profile update if True.
                Defaults to False

        Returns:
            dict: the raw profile dictionary from the Spotify API
        """
        await self.async_ensure_tokens_valid(skip_profile=True)
        LOGGER.debug("Getting Profile from Spotify")

        dataset = self._datasets["profile"]

        async with dataset.lock:
            if force or dataset.is_expired():
                LOGGER.debug("Refreshing profile dataset")
                data = await self.hass.async_add_executor_job(
                    self.apis["public"].me
                )
                dataset.update(data)
            else:
                LOGGER.debug("Using cached profile dataset")

        return self.profile
