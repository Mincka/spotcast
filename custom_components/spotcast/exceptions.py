"""Generic exceptions for spotcast."""

from homeassistant.exceptions import HomeAssistantError


class TokenError(HomeAssistantError):
    """Generic Error with the Spotify Token"""
