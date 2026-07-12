"""Module for general media player exceptions

Classes:
    - MediaPlayerError
    - MediaPlayerNotFoundError
    - UnknownIntegrationError
    - MissingActiveDeviceError
"""

from homeassistant.exceptions import HomeAssistantError


class MediaPlayerError(HomeAssistantError):
    """Generic Exceptions for Media Player"""


class MediaPlayerNotFoundError(MediaPlayerError):
    """Error raised when the player could not be found"""


class UnknownIntegrationError(MediaPlayerError):
    """The integration specified is not known for spotcast"""


class MissingActiveDeviceError(MediaPlayerError):
    """No Active device found for the account provided"""
