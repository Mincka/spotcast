"""Exceptions for the Spotify Module

Classes:
    - TokenError
    - PlaybackError
    - ExpiredDatasetError
    - SearchQueryError
    - InvalidFilterError
    - InvalidTagsError
    - InvalidItemTypeError
    - RateLimitedError
"""

from datetime import datetime
from time import time

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from spotipy.exceptions import SpotifyException

from custom_components.spotcast.exceptions import TokenError

__all__ = [
    "TokenError",
    "PlaybackError",
    "ExpiredDatasetError",
    "SearchQueryError",
    "InvalidFilterError",
    "InvalidTagsError",
    "InvalidItemTypeError",
    "RateLimitedError",
]


class PlaybackError(HomeAssistantError):
    """raised when playback failed due to an exception from Spotify"""


class ExpiredDatasetError(HomeAssistantError):
    """Raised when a dataset if retrived while expired"""


class SearchQueryError(ServiceValidationError):
    """Abstract exception for the Search Query Object"""


class InvalidFilterError(SearchQueryError):
    """Raised when a search query is built with invalid filters"""


class InvalidTagsError(SearchQueryError):
    """Raised when a search query is built with invalid filters"""


class InvalidItemTypeError(SearchQueryError):
    """Raised when a search query is built with an invalid item type"""


class RateLimitedError(SpotifyException):
    """Raised when a Spotify API call is skipped or rejected because
    the client id is currently rate limited.

    Subclass of `SpotifyException` (http status 429) so the existing
    error handling of the api callers keeps working.

    Attributes:
        - retry_at(float): epoch timestamp when calls may resume
    """

    def __init__(self, retry_at: float, url: str | None = None):
        """Raised when a Spotify API call is skipped or rejected because
        the client id is currently rate limited.

        Args:
            - retry_at(float): epoch timestamp when calls may resume
            - url(str, optional): the url of the skipped call
        """
        self.retry_at = retry_at

        super().__init__(
            429,
            -1,
            f"{url or 'Spotify API'}: rate limited until "
            f"{self.resume_time}",
            reason="rate limited",
        )

    @property
    def resume_time(self) -> str:
        """Returns the local time at which calls may resume."""
        return datetime.fromtimestamp(self.retry_at).strftime("%H:%M:%S")

    @property
    def seconds_remaining(self) -> int:
        """Returns the number of seconds until calls may resume."""
        return max(0, int(self.retry_at - time()) + 1)
