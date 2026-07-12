"""Reads through Spotify's unofficial internal endpoints.

Classes:
    InternalApiMixin
"""

from custom_components.spotcast.spotify.internal_api import (
    async_get_playlist_length,
    async_get_playlist_name,
)


class InternalApiMixin:
    """Delegates to the internal endpoint helpers, which also resolve
    editorial and algorithmic playlists that 404 on the public Web
    API."""

    async def async_get_internal_playlist_length(
        self, uri: str
    ) -> int | None:
        """Returns the track count of a playlist through Spotify's
        unofficial internal endpoint, which also resolves editorial and
        algorithmic playlists that 404 on the public Web API.

        Args:
            - uri(str): the playlist uri

        Returns:
            - int | None: the track count, or None when the internal
                endpoint is unavailable (callers should fall back)
        """
        return await async_get_playlist_length(self, uri)

    async def async_get_current_context_name(self) -> str | None:
        """Returns the human-readable name of the playlist currently
        playing on the account.

        The context uri comes from the public playback state, but its
        name is resolved through the unofficial internal endpoint so it
        also works for editorial/algorithmic playlists. The last
        resolved name is cached per context uri to avoid a lookup on
        every refresh.

        Returns:
            - str | None: the playlist name, or None when nothing is
                playing, the context is not a playlist, or the name
                could not be resolved
        """
        playback = self.playback_state
        context = (
            playback.get("context") if isinstance(playback, dict) else None
        )
        uri = context.get("uri") if isinstance(context, dict) else None

        if not uri or ":playlist:" not in uri:
            return None

        if uri == self._context_name_cache[0]:
            return self._context_name_cache[1]

        name = await async_get_playlist_name(self, uri)

        if name is not None:
            self._context_name_cache = (uri, name)

        return name
