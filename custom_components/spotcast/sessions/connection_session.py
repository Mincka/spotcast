"""Module for the abstract class ConnectionSession.

Classes:
    - ConnectionSession
"""

from abc import ABC, abstractmethod
from asyncio import Lock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .retry_supervisor import RetrySupervisor
from custom_components.spotcast.entry_data import ApiItem, EntryData
from custom_components.spotcast.utils import copy_to_dict

SUPERVISED_ERRORS = ()


class ConnectionSession(ABC):
    """Module for the abstract class ConnectionSession."""

    API_ENDPOINT = None
    API_KEY = "None"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Module for the abstract class ConnectionSession."""
        self.hass = hass
        self.entry = entry
        self._entry_data: EntryData = copy_to_dict(self.entry.data)
        self._is_healthy = False
        self._token_lock = Lock()
        self.supervisor = RetrySupervisor()

    @abstractmethod
    async def async_ensure_token_valid(self) -> ApiItem:
        """Method that ensures a token is currently valid."""

    @property
    def _data(self) -> dict:
        """Retrieves the data from the entry."""
        return self._entry_data[self.API_KEY]

    @_data.setter
    def _data(self, data: dict) -> None:
        """Saves data for the api entry."""
        self._entry_data[self.API_KEY] = data

    @property
    def token(self) -> dict:
        """Retrives the token information for the session."""
        return self._data["token"]

    @property
    def access_token(self) -> str:
        """Retrieves the access token for the session."""
        return self.token.get("access_token")

    @property
    def refresh_token(self) -> str:
        """Retrieves the access token for the session."""
        return self.token.get("refresh_token")

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
