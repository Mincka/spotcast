"""Generic exceptions for spotcast."""

from homeassistant.exceptions import HomeAssistantError


class TokenError(HomeAssistantError):
    """Generic Error with the Spotify Token"""


class LowRatioError(Exception):
    """Raised when a best fuzzy match is too low to return a result"""
