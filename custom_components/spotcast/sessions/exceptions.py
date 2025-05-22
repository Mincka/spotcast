"""Module for exceptions related to api sessions.

Classes:
    - TokenRefreshError
    - ExpiredSpotifyCookiesError
"""

from homeassistant.exceptions import HomeAssistantError

from custom_components.spotcast.spotify.exceptions import TokenError


class TokenRefreshError(TokenError):
    """Raised when a token refresh fails."""


class ExpiredSpotifyCookiesError(TokenRefreshError):
    """Raised if the sp_dc and sp_key are expired."""


class InternalServerError(HomeAssistantError):
    """Raised for 500 range errors."""

    def __init__(self, code: int, message: str) -> None:
        """Raised for 500 range errors."""
        self.code = code
        self.message = message

        super().__init__(message)


class UpstreamServerNotready(HomeAssistantError):
    """Upstream server is not ready to receive communication again."""


class TOTPError(TokenRefreshError):
    """Raised when the time based one time password is invalid."""
