"""Module for the extended spotipy client.

Classes:
    - Spotify
"""

from spotipy import Spotify as SpotipyClient


class Spotify(SpotipyClient):
    """spotipy client extended with the Spotify Web API endpoints
    introduced by the February 2026 platform changes, which spotipy
    does not wrap. The old endpoints are removed for client ids
    created after 2026-02-11 (older ids are grandfathered)."""

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
