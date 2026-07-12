"""Module for the play media service.

Functions:
    - async_play_media
"""

from logging import getLogger
from random import randint

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from spotipy import SpotifyException


from custom_components.spotcast.media_player.exceptions import (
    MissingActiveDeviceError,
)
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.utils import get_account_entry
from custom_components.spotcast.spotify.utils import (
    url_to_uri,
    suppress_playlist_404_logs,
)
from custom_components.spotcast.media_player.utils import (
    async_media_player_from_id,
)

from custom_components.spotcast.services.utils import (
    EXTRAS_SCHEMA,
    entity_from_target_selector,
)

LOGGER = getLogger(__name__)

# Spotify 404s on its own editorial/algorithmic playlists, so their track
# count is unavailable. Such playlists are always well above this many
# tracks, so a pseudo-random start within the first N keeps `random`
# meaningful without risking an out-of-range offset (see #570).
_RANDOM_FALLBACK_ITEMS = 25

PLAY_MEDIA_SCHEMA = vol.Schema(
    {
        vol.Optional("media_player"): cv.ENTITY_SERVICE_FIELDS,
        vol.Required("spotify_uri"): url_to_uri,
        vol.Optional("account"): cv.string,
        vol.Optional("data"): EXTRAS_SCHEMA,
    }
)


async def async_play_media(hass: HomeAssistant, call: ServiceCall):
    """Service to start playing media.

    Args:
        hass(HomeAssistant): the Home Assistant Instance
        call(ServiceCall): the service call data pack
    """
    uri: str = call.data.get("spotify_uri")
    account_id: str = call.data.get("account")
    media_players: dict[str, list] = call.data.get("media_player")
    extras: dict[str] = call.data.get("data")

    if extras is None:
        extras = {}

    entry = get_account_entry(hass, account_id)
    entity_id = None

    if media_players is not None:
        entity_id = entity_from_target_selector(hass, media_players)

    LOGGER.debug("Loading Spotify Account for User `%s`", account_id)
    account = await SpotifyAccount.async_from_config_entry(
        hass=hass, entry=entry
    )

    # check for track uri and switch to album with offset if necessary
    if uri is None:
        pass
    elif uri.startswith("spotify:track:"):
        track_context = extras.get("track_context")
        if track_context == "track":
            LOGGER.debug("Using track context")
        elif (
            isinstance(track_context, str)
            and track_context.startswith("spotify:")
        ):
            uri, index = await async_context_index(
                account,
                track_context,
                uri,
            )
            LOGGER.debug(
                "Switching context to `%s`, with offset %d",
                uri,
                index,
            )
            extras["offset"] = index
        else:
            uri, index = await async_track_index(account, uri)
            LOGGER.debug(
                "Switching context to song's album `%s`, with offset %d",
                uri,
                index,
            )
            extras["offset"] = index

    elif uri.startswith("spotify:episode:"):
        uri, index = await async_episode_index(account, uri)
        LOGGER.debug(
            "Switching context to episode's show `%s`, with offset %d",
            uri,
            index,
        )
        extras["offset"] = index

    elif extras.get("random", False):
        extras["offset"] = await async_random_index(account, uri)

    if entity_id is not None:
        LOGGER.debug("Getting %s from home assistant", entity_id)
    else:
        LOGGER.debug("Getting active device for account `%s`", account.name)

    try:
        media_player = await async_media_player_from_id(
            hass=hass, account=account, entity_id=entity_id
        )
    except MissingActiveDeviceError as exc:
        raise ServiceValidationError(str(exc)) from exc

    LOGGER.info(
        "Playing `%s` on `%s` for account `%s`",
        uri,
        media_player.name,
        account.id,
    )

    await account.async_play_media(media_player.id, uri, **extras)
    await account.async_apply_extras(media_player.id, extras)


async def async_episode_index(
    account: SpotifyAccount,
    uri: str,
) -> tuple[str, int]:
    """Returns the uri of a show and its index.

    Args:
        account(SpotifyAccount): The account used to fetch episode
            information
        uri(str): A show URI

    Returns:
        tuple[str, int]: A tuple containing the show uri of the
            episode and its index in the show.
    """
    episode_info = await account.async_get_episode(uri)
    show_uri = episode_info["show"]["uri"]

    show_episodes = await account.async_get_show_episodes(show_uri)

    show_episodes = [x["uri"] for x in show_episodes]

    return show_uri, show_episodes.index(uri)


async def async_track_index(
    account: SpotifyAccount, uri: str
) -> tuple[str, int]:
    """Returns the uri of the album and the index that would play the
    uri provided in the context of the album

    Args:
        - account(SpotifyAccount): the account used to fetch track
            information
        - uri(str): A track URI

    Returns:
        - tuple[str, int]: A tuple containing the album uri of the
            track and its index in the album (counting multi disc
            albums)
    """
    track_info = await account.async_get_track(uri)
    album_uri = track_info["album"]["uri"]

    # returns track number, when part of album
    if track_info["disc_number"] == 1:
        return album_uri, track_info["track_number"] - 1

    album_info = await account.async_get_album(album_uri)

    album_songs = [x["uri"] for x in album_info["tracks"]["items"]]

    return album_uri, album_songs.index(uri)


async def async_context_index(
    account: SpotifyAccount,
    context_uri: str,
    track_uri: str,
) -> tuple[str, int]:
    """Returns the context uri and the index of a track within it

    Args:
        - account(SpotifyAccount): the account used to fetch context
            information
        - context_uri(str): an album or playlist URI to play the
            track in
        - track_uri(str): the track URI to locate in the context

    Returns:
        - tuple[str, int]: the context uri and the index of the track
            within the context

    Raises:
        - ServiceValidationError: when the context type is not
            supported or the track is not part of the context
    """
    context_type = context_uri.split(":")[1]

    if context_type == "album":
        album = await account.async_get_album(context_uri)
        track_uris = [x["uri"] for x in album["tracks"]["items"]]
    elif context_type == "playlist":
        items = await account.async_get_playlist_tracks(context_uri)
        track_uris = [
            x["track"]["uri"]
            for x in items
            if x.get("track") is not None
        ]
    else:
        raise ServiceValidationError(
            f"`{context_uri}` is not a valid track context. Provide an "
            "album or playlist URI."
        )

    if track_uri not in track_uris:
        raise ServiceValidationError(
            f"Track `{track_uri}` is not part of the context "
            f"`{context_uri}`"
        )

    return context_uri, track_uris.index(track_uri)


async def _async_editorial_random_index(
    account: SpotifyAccount, uri: str
) -> int:
    """Returns a random start index for a playlist the public Web API
    would not resolve (typically an editorial/algorithmic playlist).

    It first tries Spotify's unofficial internal endpoint to get the real
    track count and pick a genuinely random index across the whole
    playlist. If that endpoint is unavailable, it keeps the previous
    behaviour of a pseudo-random offset within the first few tracks.
    """
    length = await account.async_get_internal_playlist_length(uri)
    if length is not None and length > 0:
        LOGGER.debug(
            "Resolved %d tracks for playlist `%s` through the internal "
            "endpoint; using a random start offset across the playlist.",
            length,
            uri,
        )
        return randint(0, length - 1)

    LOGGER.warning(
        "Could not determine the track count for playlist `%s` (likely a "
        "Spotify editorial/algorithmic playlist no longer exposed through "
        "the Web API, with the internal endpoint unavailable). Using a "
        "pseudo-random start offset within the first %d tracks.",
        uri,
        _RANDOM_FALLBACK_ITEMS,
    )
    return randint(0, _RANDOM_FALLBACK_ITEMS - 1)


async def async_random_index(account: SpotifyAccount, uri: str) -> int:
    """Returns a random index for starting the context at. Must be an
    artist, album or playlist

    Args:
        - account(SpotifyAccount): the account used for fetching
            context info
        - uri(str): the uri of the context to start at a random index

    Result:
        - int: a random index between 0 and the number of items in the
            context uri - 1
    """

    if uri.startswith("spotify:album:"):
        album = await account.async_get_album(uri)
        count = album["total_tracks"]
    elif uri.startswith("spotify:playlist:"):
        try:
            with suppress_playlist_404_logs():
                playlist = await account.async_get_playlist(uri)
            tracks = playlist.get("tracks") or playlist.get("items") or {}
            count = tracks.get("total")
            if count is None:
                return await _async_editorial_random_index(account, uri)
        except SpotifyException as exc:
            if exc.http_status != 404:
                raise
            return await _async_editorial_random_index(account, uri)
    elif uri == account.liked_songs_uri:
        count = await account.async_liked_songs_count()
    else:
        raise ServiceValidationError(
            f"{uri} is not compatible with random start track"
        )

    return randint(0, count - 1)
