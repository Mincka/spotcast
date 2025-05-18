"""Module for the abstract class ConnectionSession

Classes:
    - ConnectionSession
"""

from abc import ABC, abstractmethod
from asyncio import Lock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .retry_supervisor import RetrySupervisor
from custom_components.spotcast.entry_data import EntryData

SUPERVISED_ERRORS = ()


class ConnectionSession(ABC):
    API_ENDPOINT = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._is_healthy = False
        self._token_lock = Lock()
        self.supervisor = RetrySupervisor()

    @abstractmethod
    async def async_ensure_token_valid(self):
        """Method that ensures a token is currently valid"""

    @property
    @abstractmethod
    def token(self) -> str:
        """Retrives the token for the session"""

    @property
    @abstractmethod
    def clean_token(self) -> str:
        """returns the currently valid token only, no additional
        information"""

    @property
    def is_healthy(self) -> bool:
        """Returns True if the session is able to refresh its token"""
        return self.supervisor.is_healthy
