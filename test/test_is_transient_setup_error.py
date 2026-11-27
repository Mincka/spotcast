"""Module to test the is_transient_setup_error function"""

from time import time
from unittest import TestCase
from unittest.mock import MagicMock

from aiohttp.client_exceptions import (
    ClientConnectorError,
    ClientResponseError,
    ServerTimeoutError,
)
from requests import Response
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
    HTTPError,
    ReadTimeout,
    RetryError,
)
from spotipy import SpotifyException

from custom_components.spotcast import is_transient_setup_error
from custom_components.spotcast.sessions.exceptions import (
    InternalServerError,
    TokenRefreshError,
    UpstreamServerNotready,
)
from custom_components.spotcast.spotify.exceptions import RateLimitedError


def client_response_error(status: int) -> ClientResponseError:
    return ClientResponseError(MagicMock(), (), status=status)


def http_error(status: int) -> HTTPError:
    response = Response()
    response.status_code = status
    return HTTPError(response=response)


class TestTransientErrors(TestCase):

    def test_transient(self):
        errors = {
            "requests read timeout": ReadTimeout("Read timed out"),
            "requests connection error": RequestsConnectionError("DNS"),
            "requests retry error": RetryError("max retries"),
            "aiohttp connector error": ClientConnectorError(
                MagicMock(), OSError("unreachable")
            ),
            "aiohttp timeout": ServerTimeoutError("timeout"),
            "asyncio timeout": TimeoutError(),
            "token endpoint not ready": UpstreamServerNotready("not ready"),
            "internal server error": InternalServerError(503, "down"),
            "spotify 502": SpotifyException(502, -1, "Bad Gateway"),
            "spotify 429": SpotifyException(429, -1, "Too Many Requests"),
            "spotipy fake 429": SpotifyException(
                429, -1, "url", reason="too many 502 error responses"
            ),
            "rate limit guard": RateLimitedError(time() + 30),
            "token endpoint 503": client_response_error(503),
            "token endpoint 429": client_response_error(429),
            "raw http 500": http_error(500),
        }

        for name, exc in errors.items():
            with self.subTest(name):
                self.assertTrue(is_transient_setup_error(exc))


class TestPermanentErrors(TestCase):

    def test_permanent(self):
        errors = {
            "spotify 401": SpotifyException(401, -1, "Unauthorized"),
            "spotify 403": SpotifyException(403, -1, "Forbidden"),
            "spotify 404": SpotifyException(404, -1, "Not Found"),
            "spotify without status": SpotifyException(None, -1, "?"),
            "token endpoint 401": client_response_error(401),
            "token endpoint 403": client_response_error(403),
            "raw http 401": http_error(401),
            "token refresh error": TokenRefreshError("revoked"),
            "programming error": KeyError("profile"),
            "value error": ValueError("Implementation not available"),
        }

        for name, exc in errors.items():
            with self.subTest(name):
                self.assertFalse(is_transient_setup_error(exc))
