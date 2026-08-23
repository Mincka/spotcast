"""Module for the extended spotipy client.

Classes:
    - Spotify
"""

from collections.abc import Callable
from logging import getLogger
from re import compile as re_compile
from typing import Any

from requests import Session
from requests.adapters import HTTPAdapter
from spotipy import Spotify as SpotipyClient
from spotipy.exceptions import SpotifyException
from urllib3.util.retry import Retry

from custom_components.spotcast.spotify.exceptions import RateLimitedError
from custom_components.spotcast.spotify.rate_limit import (
    RATE_LIMIT_GUARD,
    RateLimitGuard,
)

LOGGER = getLogger(__name__)

# spotipy retries 429 responses by sleeping the full `Retry-After`
# inside the calling (executor) thread, up to 3 times, which can block
# a Home Assistant worker for hours. Rate limits are handled by the
# shared guard instead; only server errors are left to the retry
# adapter, with a short exponential backoff.
SERVER_ERROR_RETRY_CODES = (500, 502, 503, 504)

# spotipy hard-codes http status 429 when its retries are exhausted,
# even when the retried responses were 5xx server errors (see
# spotipy-dev/spotipy#805). The real status is in the reason.
SERVER_ERROR_PATTERN = re_compile(r"too many 5\d\d error responses")


def is_rate_limit(exc: SpotifyException) -> bool:
    """Returns True if the exception is a genuine rate limit response,
    as opposed to spotipy's fake 429 for exhausted 5xx retries."""
    return exc.http_status == 429 and not (
        exc.reason is not None
        and SERVER_ERROR_PATTERN.search(str(exc.reason))
    )


class Spotify(SpotipyClient):
    """spotipy client extended with the Spotify Web API endpoints
    introduced by the February 2026 platform changes, which spotipy
    does not wrap. The old endpoints are removed for client ids
    created after 2026-02-11 (older ids are grandfathered).

    Also retries once with a freshly refreshed token when the API
    rejects a token the session still considers valid, and honours the
    integration wide rate limit guard: a 429 pauses every client
    sharing the guard until the `Retry-After` window expires, without
    blocking the executor thread.
    """

    def __init__(
        self,
        *args,
        token_refresher: Callable[[], str] | None = None,
        rate_limit_guard: RateLimitGuard | None = None,
        **kwargs,
    ):
        """Constructor of the extended spotipy client.

        Args:
            token_refresher(Callable, optional): Called from the
                executor thread to obtain a freshly refreshed access
                token after a 401. Retries are disabled when omitted.
            rate_limit_guard(RateLimitGuard, optional): the shared
                rate limit state. Defaults to the integration wide
                guard.
        """
        kwargs.setdefault("status_forcelist", SERVER_ERROR_RETRY_CODES)
        super().__init__(*args, **kwargs)
        self._token_refresher = token_refresher
        self._rate_limit_guard = rate_limit_guard or RATE_LIMIT_GUARD

    def _build_session(self):
        """Builds the requests session with a retry adapter that never
        sleeps on a `Retry-After` header.

        Removing 429 from `status_forcelist` is not enough: urllib3
        also retries any 429/503 that carries a `Retry-After` header
        when `respect_retry_after_header` is set (the default), and
        spotipy's own session builder gives no way to turn it off.
        """
        self._session = Session()
        retry = Retry(
            total=self.retries,
            connect=None,
            read=False,
            allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
            status=self.status_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
            respect_retry_after_header=False,
        )

        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _internal_call(
        self,
        method: str,
        url: str,
        payload: Any,
        params: dict,
    ) -> Any:
        """Performs the api call, retrying once on an unexpected 401.

        A 401 is expected when the token is expired, but the account
        refreshes it before every call. Spotify still occasionally
        rejects a valid token, in which case a forced refresh recovers
        instead of surfacing the failure to the user.

        Raises:
            - RateLimitedError: raised without any network call while
                the shared rate limit is active, or after a 429
                response, which registers the new window.
        """
        self._rate_limit_guard.check()

        try:
            return super()._internal_call(method, url, payload, params)
        except RateLimitedError:
            raise
        except SpotifyException as exc:
            if is_rate_limit(exc):
                raise self._rate_limited(exc, url) from exc

            if exc.http_status != 401 or self._token_refresher is None:
                raise

            LOGGER.warning(
                "Spotify rejected the access token for %s. Forcing a "
                "token refresh and retrying once",
                url,
            )

            try:
                token = self._token_refresher()
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception(
                    "Could not refresh the access token after a 401"
                )
                raise exc from None

            self.set_auth(token)

            try:
                return super()._internal_call(method, url, payload, params)
            except SpotifyException as retry_exc:
                if is_rate_limit(retry_exc):
                    raise self._rate_limited(retry_exc, url) from retry_exc
                raise

    def _rate_limited(
        self,
        exc: SpotifyException,
        url: str,
    ) -> RateLimitedError:
        """Registers a 429 with the shared guard and builds the error
        raised in its place. A missing `Retry-After` falls back to the
        guard's default window.
        """
        headers = exc.headers or {}
        retry_at = self._rate_limit_guard.register(headers.get("Retry-After"))

        return RateLimitedError(retry_at, url)

    def save_to_library(self, uris: list[str]) -> dict:
        """Saves a list of Spotify URIs to the user's library.

        Replacement for the removed `PUT /me/tracks` endpoint. The
        endpoint only accepts the uris as query parameters.
        """
        return self._put(f"me/library?uris={','.join(uris)}")

    def remove_from_library(self, uris: list[str]) -> dict:
        """Removes a list of Spotify URIs from the user's library.

        Replacement for the removed `DELETE /me/tracks` endpoint.
        """
        return self._delete(f"me/library?uris={','.join(uris)}")

    # Intentionally narrower than spotipy's signature: the new endpoint
    # does not support the removed `additional_types` argument.
    def playlist_items(  # pylint: disable=arguments-differ
        self,
        playlist_id: str,
        fields: str = None,
        limit: int = 100,
        offset: int = 0,
        market: str = None,
    ) -> dict:
        """Retrieves the items of a playlist.

        Replacement for the removed `GET /playlists/{id}/tracks`
        endpoint. Same signature and pagination shape as spotipy's
        `playlist_tracks`.
        """
        playlist_id = self._get_id("playlist", playlist_id)

        return self._get(
            f"playlists/{playlist_id}/items",
            fields=fields,
            limit=limit,
            offset=offset,
            market=market,
        )
