"""Module for exceptions related to api sessions.

Classes:
    - TokenRefreshError
"""

from homeassistant.exceptions import HomeAssistantError

from custom_components.spotcast.spotify.exceptions import TokenError


class TokenRefreshError(TokenError):
    """Raised when a token refresh fails."""


class InternalServerError(HomeAssistantError):
    """Raised for 500 range errors."""

    def __init__(self, code: int, message: str) -> None:
        """Raised for 500 range errors."""
        self.code = code
        self.message = message

        super().__init__(message)


class UpstreamServerNotready(HomeAssistantError):
    """Upstream server is not ready to receive communication again."""
