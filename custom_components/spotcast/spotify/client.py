"""Module for the extended spotipy client.

Classes:
    - Spotify
"""

from collections.abc import Callable
from logging import getLogger
from typing import Any

from spotipy import Spotify as SpotipyClient
from spotipy.exceptions import SpotifyException

LOGGER = getLogger(__name__)


class Spotify(SpotipyClient):
    """spotipy client extended with the Spotify Web API endpoints
    introduced by the February 2026 platform changes, which spotipy
    does not wrap. The old endpoints are removed for client ids
    created after 2026-02-11 (older ids are grandfathered).

    Also retries once with a freshly refreshed token when the API
    rejects a token the session still considers valid.
    """

    def __init__(
        self,
        *args,
        token_refresher: Callable[[], str] | None = None,
        **kwargs,
    ):
        """Constructor of the extended spotipy client.

        Args:
            token_refresher(Callable, optional): Called from the
                executor thread to obtain a freshly refreshed access
                token after a 401. Retries are disabled when omitted.
        """
        super().__init__(*args, **kwargs)
        self._token_refresher = token_refresher

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
        """
        try:
            return super()._internal_call(method, url, payload, params)
        except SpotifyException as exc:
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

            return super()._internal_call(method, url, payload, params)

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
