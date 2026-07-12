"""Exceptions for the Spotify Module

Classes:
    - TokenError
    - PlaybackError
    - ExpiredDatasetError
    - SearchQueryError
    - InvalidFilterError
    - InvalidTagsError
    - InvalidItemTypeError
"""

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.spotcast.exceptions import TokenError


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
