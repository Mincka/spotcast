"""Custom implementation of the OAuth2Session for Spotcast.

Classes:
    - PublicSession

Functions:
    - async_get_config_entry_implementation
"""

from logging import getLogger
from typing import Any, cast

from homeassistant.helpers.config_entry_oauth2_flow import (
    client,
    async_oauth2_request,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2Implementation,
    async_get_implementations,
)

from custom_components.spotcast.entry_data import TokenData

from .connection_session import ConnectionSession

LOGGER = getLogger(__name__)


class PublicSession(ConnectionSession):
    """Custom implementation of the OAuth2Session for Spotcast.

    Properties:
        - token(dict): The current token for the public spotify api

    Methods:
        - async_ensure_token_valid
        - async_request
    """

    API_ENDPOINT = "https://api.spotify.com"
    API_KEY = "external_api"
    SESSION_TYPE = "Public"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        implementation: AbstractOAuth2Implementation,
    ) -> None:
        """Initialize an OAuth2 session."""
        self.implementation = implementation
        super().__init__(hass, entry)

    async def async_refresh_token(self) -> TokenData:
        """Refreshes the token and returns its new data."""
        token = await self.implementation.async_refresh_token(self.token)
        return cast("TokenData", token)

    async def async_request(
        self,
        method: str,
        url: str,
        **kwargs: dict[Any, Any],
    ) -> client.ClientResponse:
        """Make a request."""
        await self.async_ensure_token_valid()
        return await async_oauth2_request(
            self.hass,
            self.token,
            method,
            url,
            **kwargs,
        )


async def async_get_config_entry_implementation(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> AbstractOAuth2Implementation:
    """Return the implementation for this config entry."""
    implementations = await async_get_implementations(
        hass,
        config_entry.domain,
    )

    implementation = implementations.get(
        config_entry.data[PublicSession.API_KEY]["auth_implementation"]
    )

    if implementation is None:
        raise ValueError("Implementation not available")

    return implementation
