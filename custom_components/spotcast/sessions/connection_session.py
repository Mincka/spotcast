"""Module for the abstract class ConnectionSession.

Classes:
    - ConnectionSession
"""

from abc import ABC, abstractmethod
from asyncio import Lock
from logging import getLogger
from time import time
from typing import cast, Literal

from aiohttp.client_exceptions import ClientResponseError
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .retry_supervisor import RetrySupervisor
from custom_components.spotcast.entry_data import ApiItem, EntryData, TokenData
from custom_components.spotcast.utils import copy_to_dict

from .exceptions import UpstreamServerNotready, TokenRefreshError

LOGGER = getLogger(__name__)


class ConnectionSession(ABC):
    """Module for the abstract class ConnectionSession."""

    API_ENDPOINT: str | None = None
    API_KEY: Literal["desktop_api", "external_api"]
    EXPIRATION_OFFSET = 600
    SESSION_TYPE = "Dummy"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Module for the abstract class ConnectionSession."""
        self.hass = hass
        self.entry = entry
        self._entry_data: EntryData = cast(
            "EntryData",
            copy_to_dict(self.entry.data),
        )
        self._token_lock = Lock()
        self.supervisor = RetrySupervisor()

    @property
    def expires_at(self) -> float:
        """Returns the expiration epoch of the access token."""
        return self.token["expires_at"]

    @property
    def valid_token(self) -> bool:
        """Returns False if the access token is expired."""
        return self.expires_at - self.EXPIRATION_OFFSET > time()

    @property
    def data(self) -> ApiItem:
        """Retrieves the data from the entry."""
        return cast(
            "ApiItem",
            self._entry_data[self.API_KEY],
        )

    @data.setter
    def data(self, data: ApiItem) -> None:
        """Saves data for the api entry."""
        self._entry_data[self.API_KEY] = data

    @property
    def token(self) -> TokenData:
        """Retrieves the token information for the session."""
        return self.data["token"]

    @token.setter
    def token(self, data: TokenData) -> None:
        """Updates the token data."""
        self.data["token"] = data

    @property
    def access_token(self) -> str:
        """Retrieves the access token for the session."""
        return self.token["access_token"]

    @property
    def refresh_token(self) -> str:
        """Retrieves the access token for the session."""
        return self.token["refresh_token"]

    @property
    def obfuscated_token(self) -> str | None:
        """Returns a token with data hidden for anonimity.

        Used mostly in logs
        """
        padding = 3
        inner_string = "*" * 20

        return (
            f"{self.access_token[:padding]}"
            f"{inner_string}"
            f"{self.access_token[-padding:]}"
        )

    @property
    def is_healthy(self) -> bool:
        """Returns True if the session is able to refresh its token."""
        return self.supervisor.is_healthy

    @abstractmethod
    async def async_refresh_token(self) -> TokenData:
        """Refreshes the token and returns its new data.

        The token data must include an `expires_at` key, not the
        `expires_in` standard key.
        """

    async def async_ensure_token_valid(self) -> bool:
        """Method that ensures a token is currently valid.

        Returns:
            bool: Returns `True` if the token was refreshed and `False`
                if not
        """
        async with self._token_lock:
            if self.valid_token:
                return False

            if not self.supervisor.is_ready:
                raise UpstreamServerNotready("Server not ready for refresh")

            LOGGER.debug(
                "%s Session - Expired Token `%s`",
                self.SESSION_TYPE,
                self.obfuscated_token,
            )

            try:
                api_response = await self.async_refresh_token()
            except self.supervisor.SUPERVISED_EXCEPTIONS as exc:
                self.supervisor.is_healthy = False
                self.supervisor.log_message(exc)
                raise UpstreamServerNotready(
                    "Server not ready for refresh"
                ) from exc
            except ClientResponseError as exc:
                self.supervisor.is_healthy = False
                if exc.status == 400:
                    LOGGER.error("Unable to refresh desktop token")
                    raise TokenRefreshError(exc) from exc
                raise exc from exc

            self.supervisor.is_healthy = True
            self.token = api_response
            LOGGER.debug(
                "%s Session - New Token `%s`",
                self.SESSION_TYPE,
                self.obfuscated_token,
            )

            return True
