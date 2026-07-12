"""Access to Spotify's unofficial internal endpoints.

These endpoints back the desktop and web players. They are not part of
the public Web API, are reached with the desktop application token, and
are unsupported by Spotify: they may change or disappear without notice.
Every helper therefore degrades gracefully (returns None) instead of
raising, so callers can fall back to supported behaviour.

Functions:
    async_get_playlist_length
    async_get_playlist_name
"""

from logging import getLogger

from aiohttp import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

LOGGER = getLogger(__name__)

SPCLIENT_BASE = "https://spclient.wg.spotify.com"


async def _async_get_playlist_metadata(account, uri: str) -> dict | None:
    """Fetches a playlist's metadata document from the internal endpoint.

    Unlike the public Web API, this endpoint also resolves Spotify's own
    editorial/algorithmic playlists (the ones that 404 publicly).

    Args:
        - account(SpotifyAccount): the account whose desktop token
            authorises the call
        - uri(str): the playlist uri or bare id

    Returns:
        - dict | None: the parsed metadata, or None if it could not be
            retrieved through the internal endpoint
    """
    playlist_id = uri.rsplit(":", 1)[-1]
    url = f"{SPCLIENT_BASE}/playlist/v2/playlist/{playlist_id}/metadata"

    try:
        token = await account.async_get_token("private")
    except Exception as exc:  # pylint: disable=broad-except
        # The desktop session is optional and its failures must never
        # break the caller; fall back instead.
        LOGGER.debug("Desktop token unavailable for internal API: %s", exc)
        return None

    session = async_get_clientsession(account.hass)
    headers = {
        "authorization": f"Bearer {token}",
        "accept": "application/json",
    }

    try:
        response = await session.get(url, headers=headers)
    except ClientError as exc:
        LOGGER.debug("Internal playlist metadata request failed: %s", exc)
        return None

    if response.status != 200:
        LOGGER.debug(
            "Internal playlist metadata returned %d for `%s`",
            response.status,
            uri,
        )
        return None

    try:
        data = await response.json(content_type=None)
    except (ClientError, ValueError) as exc:
        LOGGER.debug(
            "Internal playlist metadata returned invalid JSON: %s", exc
        )
        return None

    return data if isinstance(data, dict) else None


async def async_get_playlist_length(account, uri: str) -> int | None:
    """Returns the number of tracks in a playlist using the internal
    playlist metadata endpoint.

    Args:
        - account(SpotifyAccount): the account whose desktop token
            authorises the call
        - uri(str): the playlist uri or bare id

    Returns:
        - int | None: the track count, or None if it could not be
            determined through the internal endpoint
    """
    data = await _async_get_playlist_metadata(account, uri)

    if data is None:
        return None

    length = data.get("length")
    return length if isinstance(length, int) else None


async def async_get_playlist_name(account, uri: str) -> str | None:
    """Returns the human-readable name of a playlist using the internal
    playlist metadata endpoint. Resolves editorial/algorithmic playlists
    that carry no name through the public Web API.

    Args:
        - account(SpotifyAccount): the account whose desktop token
            authorises the call
        - uri(str): the playlist uri or bare id

    Returns:
        - str | None: the playlist name, or None if it could not be
            determined through the internal endpoint
    """
    data = await _async_get_playlist_metadata(account, uri)

    if data is None:
        return None

    attributes = data.get("attributes")
    name = attributes.get("name") if isinstance(attributes, dict) else None
    return name if isinstance(name, str) and name != "" else None
