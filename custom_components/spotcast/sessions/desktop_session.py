"""An API session through the spotify desktop oauth application."""

from json import JSONDecodeError
from logging import getLogger
from time import time

from aiohttp.client_exceptions import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.spotcast.const import DOMAIN, SPOTIFY_CLIENT_ID
from custom_components.spotcast.entry_data import ApiItem, EntryData
from custom_components.spotcast.utils import copy_to_dict

from .connection_session import ConnectionSession, HomeAssistant, ConfigEntry
from .exceptions import UpstreamServerNotready

LOGGER = getLogger(__name__)


class DesktopSession(ConnectionSession):
    """An API session through the spotify desktop oauth application."""

    BASE_URL = "https://accounts.spotify.com"
    TOKEN_ENDPOINT = "api/token"
    EXPIRATION_OFFSET = -600

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """An API session through the spotify desktop oauth application."""
        self._entry_data: EntryData = copy_to_dict(entry.data)
        super().__init__(hass, entry)

    @property
    def _data(self) -> ApiItem:
        return self._entry_data["desktop_api"]

    @property
    def token(self) -> str:
        """Returns the active token for the session."""
        return self._data["token"]["access_token"]

    @property
    def obfuscated_token(self) -> str:
        """Returns a token with data hidden for anonimity.

        Used mostly in logs
        """
        padding = 3
        inner_string = "*" * 20
        return f"{self.token[:padding]}{inner_string}{self.token[-padding:]}"

    @property
    def clean_token(self) -> str:
        """Returns the active token for the session."""
        return self.token

    @property
    def refresh_token(self) -> str:
        """The refresh token for the api."""
        return self._data["token"]["refresh_token"]

    @property
    def expires_at(self) -> int:
        """Returns the timestamp of when the access token will expire."""
        return self._data["token"]["expires_at"]

    @property
    def valid_token(self) -> bool:
        """Returns True if the token is still valid."""
        return self.expires_at + self.EXPIRATION_OFFSET > time()

    async def async_ensure_token_valid(self):
        """Checks if the token is valid and if not refreshes it."""
        not_ready = False

        async with self._token_lock:
            if self.valid_token:
                return

            if not self.supervisor.is_ready:
                not_ready = True

            else:
                LOGGER.debug(
                    "Token `%s` is expired. Getting a new one",
                    self.obfuscated_token,
                )

                try:
                    api_response = await self.async_refresh_token()
                    self.supervisor.is_healthy = True

                    self._entry_data["desktop_api"]["token"] = api_response
                    LOGGER.debug(
                        "New token received: `%s`",
                        self.obfuscated_token,
                    )

                    self.hass.config_entries.async_update_entry(
                        self.entry,
                        data=self._entry_data,
                    )
                except self.supervisor.SUPERVISED_EXCEPTIONS as exc:
                    self.supervisor.is_healthy = False
                    self.supervisor.log_message(exc)
                    not_ready = True

        if not_ready:
            raise UpstreamServerNotready("Server not ready for refresh")

    async def async_refresh_token(self) -> ApiItem:
        """Refreshes the token."""
        session = async_get_clientsession(self.hass)

        data = {
            "grant_type": "refresh_token",
            "client_id": SPOTIFY_CLIENT_ID,
            "refresh_token": self.refresh_token,
        }

        response = await session.post(
            url=f"{self.BASE_URL}/{self.TOKEN_ENDPOINT}",
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
