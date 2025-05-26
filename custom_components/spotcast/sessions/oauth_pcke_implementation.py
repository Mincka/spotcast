"""Custom OAuth2 with PCKE flow that uses a local relay server."""

from base64 import urlsafe_b64encode
from hashlib import sha256
from logging import getLogger
from time import time
from os import urandom

from homeassistant.helpers.config_entry_oauth2_flow import (
    LocalOAuth2ImplementationWithPkce,
)

from custom_components.spotcast.entry_data import (
    TokenData,
    SpotifyTokenResponse,
)

LOGGER = getLogger(__name__)


class RelayedOAuth2ImplementationWithPcke(LocalOAuth2ImplementationWithPkce):
    """Custom OAuth2 with PCKE flow that uses a local relay server."""

    SCOPES = [
        "streaming",
        "app-remote-control",
        "playlist-modify",
        "playlist-read",
        "user-modify",
        "user-modify-private",
        "user-personalized",
        "user-read-birthdate",
        "user-read-play-history",
        "user-read-playback-state",
        "user-read-email",
    ]

    @property
    def redirect_uri(self) -> str:
        """Returns the redirect uri."""
        return "http://127.0.0.1:8080/login"

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data to be included in the authorize request."""
        data = {"scope": " ".join(self.SCOPES)}
        data.update(super().extra_authorize_data)

        return data

    @property
    def extra_token_resolve_data(self) -> dict:
        """Extra data to be included in the token resolve request."""
        data = {"client_id": self.client_id}
        data.update(super().extra_token_resolve_data)
        return data

    async def async_resolve_external_data(
        self,
        external_data: dict,
    ) -> TokenData:
        """Resolve the authorization code to tokens."""
        request_data: dict = {
            "grant_type": "authorization_code",
            "code": external_data["code"],
            "redirect_uri": external_data["state"]["redirect_uri"],
        }
        request_data.update(self.extra_token_resolve_data)

        result: SpotifyTokenResponse = await self._token_request(request_data)
        result["expires_at"] = result.pop("expires_in") + time()
        return result

    @staticmethod
    def generate_code_verifier(_: int = 128) -> str:
        """Generate a code verifier."""
        return urlsafe_b64encode(urandom(64)).rstrip(b"=").decode()

    @staticmethod
    def compute_code_challenge(code_verifier: str) -> str:
        """Computes the code challenge."""
        digest = sha256(code_verifier.encode()).digest()
        return urlsafe_b64encode(digest).rstrip(b"=").decode()
