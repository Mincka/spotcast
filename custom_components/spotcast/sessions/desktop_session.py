"""An API session through the spotify desktop oauth application."""

from json import JSONDecodeError
from logging import getLogger
from time import time

from aiohttp.client_exceptions import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.spotcast.const import DOMAIN, SPOTIFY_CLIENT_ID
from custom_components.spotcast.entry_data import ApiItem

from .connection_session import ConnectionSession

LOGGER = getLogger(__name__)


class DesktopSession(ConnectionSession):
    """An API session through the spotify desktop oauth application."""

    API_ENDPOINT = "https://accounts.spotify.com"
    TOKEN_ENDPOINT = "api/token"
    API_KEY = "desktop_api"
    SESSION_TYPE = "Desktop"

    async def async_refresh_token(self) -> ApiItem:
        """Refreshes the token."""
        session = async_get_clientsession(self.hass)

        data = {
            "grant_type": "refresh_token",
            "client_id": SPOTIFY_CLIENT_ID,
            "refresh_token": self.refresh_token,
        }

        response = await session.post(
            url=f"{self.API_ENDPOINT}/{self.TOKEN_ENDPOINT}",
            data=data,
        )

        if response.status >= 400:
            try:
                error_response = await response.json()
            except (ClientError, JSONDecodeError):
                error_response = {}

            error_code = error_response.get("error", "unknown")
            error_description = error_response.get(
                "error_description",
                "unknown_error",
            )
            LOGGER.error(
                "Token request for %s failed (%s): %s",
                DOMAIN,
                error_code,
                error_description,
            )

        response.raise_for_status()
        data = await response.json()

        # sets the new expires at key
        data["expires_at"] = data.pop("expires_in") + time()
        return data
